#!/usr/bin/env python3
"""
MARTA Poetry Audio Stream Generator
=====================================
Produces an ~60-minute MP3 audio stream of randomly selected poems, each
with a unique voice and a full hybrid soundscape (SF2 bass + vibraphone,
synthesized drone/pad/heartbeat/texture layers).

Opening and closing statement:
    "You are listening to The MARTA Transit Poetry Project, AI poetry based
     on bus and train routes of the Metropolitan Atlanta Rapid Transit
     Association. Created by ThoriumCat. Embrace the strange."

Requirements:
    sudo apt-get install fluidsynth
    pip install pyfluidsynth mido openai pydub python-dotenv numpy scipy

Run:
    python3 stream_generator.py
    python3 stream_generator.py --duration 90   # target minutes
    python3 stream_generator.py --seed 1234      # reproducible shuffle
"""

import argparse, hashlib, json, os, re, sys, tempfile, time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import signal as sp_signal
import fluidsynth
from pydub import AudioSegment
from pydub.effects import normalize
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
SAMPLE_RATE      = 44100
TTS_SPEED        = 0.85
TTS_MODEL        = "tts-1"
SF2_PATH         = "/usr/share/sounds/sf2/TimGM6mb.sf2"
GM_BASS_ACOUSTIC = 32   # Acoustic Bass (upright)
GM_VIBRAPHONE    = 11   # Vibraphone
GM_MARIMBA       = 12   # Marimba
GM_STEEL_GUITAR  = 25   # Acoustic Guitar (Steel) — strum attacks
GM_STRINGS       = 48   # String Ensemble 1 — sustained warmth

STREAM_VOICES    = ["nova", "shimmer", "alloy", "echo", "fable", "onyx"]
ANNOUNCE_VOICE   = "onyx"   # deep, authoritative base voice for announcements
ROBOT_CARRIER_HZ = 90       # ring-mod carrier — 80-100 Hz = classic robot
ROBOT_BITDEPTH   = 10       # bit-crush depth (higher = subtler; 8-12 keeps speech clear)
ROBOT_RINGMOD_WET = 0.45    # 0=dry, 1=full ring-mod; blend keeps words intelligible
ANNOUNCEMENT_BODY = (
    "You are listening to The MARTA Transit Poetry Project… "
    "AI poetry based on bus and train routes of the Metropolitan Atlanta "
    "Rapid Transit Association… Created by ThoriumCat."
)
ANNOUNCEMENT_CLOSE = "Embrace the strange."
ANNOUNCEMENT_PAUSE_MS = 1000   # silence before "Embrace the strange."

CROSSFADE_MS     = 3_000    # crossfade between poem segments
MIN_POEM_WORDS   = 20       # filter out very short/stub poems
LINE_PAUSE_MEAS  = 1
STANZA_PAUSE_MEAS = 2
INTRO_MEAS       = 4
OUTRO_MEAS       = 8


# ─────────────────────────────────────────────────────────────────────────────
# Time grid
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TimeGrid:
    bpm: float
    beats_per_measure: int
    beat_unit: int

    @property
    def beat_sec(self):   return 60.0 / self.bpm
    @property
    def measure_sec(self): return self.beat_sec * self.beats_per_measure

    def beats(self, n):   return n * self.beat_sec
    def measures(self, n): return n * self.measure_sec
    def beats_ms(self, n): return int(self.beats(n) * 1000)
    def measures_ms(self, n): return int(self.measures(n) * 1000)
    def samples(self, sec): return int(sec * SAMPLE_RATE)

    def __str__(self):
        bs, ms = self.beat_sec, self.measure_sec
        return (f"{self.bpm:.0f} BPM  {self.beats_per_measure}/{self.beat_unit}"
                f"  | 1 beat={bs*1000:.0f}ms | 1 measure={ms:.2f}s")


def get_time_grid(personality: dict, char: dict, tod: str) -> TimeGrid:
    tod_bpm = {
        "morning_rush": 90, "afternoon": 72, "evening_rush": 76,
        "late_night": 44,   "night":     52, "early_morning": 58,
    }
    bpm = tod_bpm.get(tod, 60)
    prefs      = personality.get("sound_preferences", {})
    alignment  = char.get("alignment", "neutral").lower()
    tone       = char.get("tone", "neutral").lower()
    quirks     = char.get("quirks", [])
    mode       = personality.get("route_mode", "bus")
    syncopation = prefs.get("syncopation", 0.0)
    if "compulsively syncopates" in quirks:
        beats, unit = 6, 8
    elif syncopation > 0.6:
        beats, unit = 5, 4
    elif "chaotic" in alignment and syncopation > 0.3:
        beats, unit = 7, 8
    elif "dreamy" in tone:
        beats, unit = 3, 4
    elif mode == "train":
        beats, unit = 4, 4
    else:
        beats, unit = 4, 4
    return TimeGrid(bpm=bpm, beats_per_measure=beats, beat_unit=unit)


# ─────────────────────────────────────────────────────────────────────────────
# SF2 rendering helper
# ─────────────────────────────────────────────────────────────────────────────
def hz_to_midi(freq_hz: float) -> int:
    return max(0, min(127, int(round(69 + 12 * np.log2(freq_hz / 440.0)))))


def render_sf2_layer(
    sf2_path: str,
    events: list,
    total_samples: int,
    gm_program: int,
    sample_rate: int = SAMPLE_RATE,
    gain: float = 0.6,
) -> np.ndarray:
    timeline = []
    for start_sec, dur_sec, note, vel in events:
        on_samp  = int(start_sec * sample_rate)
        off_samp = int((start_sec + dur_sec) * sample_rate)
        timeline.append((on_samp,  True,  note, vel))
        timeline.append((off_samp, False, note, vel))
    timeline.sort(key=lambda x: x[0])

    fs  = fluidsynth.Synth(gain=gain, samplerate=float(sample_rate))
    sfid = fs.sfload(sf2_path)
    fs.program_select(0, sfid, 0, gm_program)

    buf    = np.zeros(total_samples, dtype=np.float32)
    cursor = 0
    for pos_samp, is_on, note, vel in timeline:
        if pos_samp > cursor:
            chunk = pos_samp - cursor
            raw   = fs.get_samples(chunk)
            stereo = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            mono   = (stereo[0::2] + stereo[1::2]) / 2.0
            end    = min(cursor + chunk, total_samples)
            buf[cursor:end] += mono[: end - cursor]
            cursor = pos_samp
        if cursor >= total_samples:
            break
        if is_on:
            fs.noteon(0, note, vel)
        else:
            fs.noteoff(0, note)

    if cursor < total_samples:
        tail = total_samples - cursor
        raw  = fs.get_samples(tail)
        stereo = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        mono   = (stereo[0::2] + stereo[1::2]) / 2.0
        buf[cursor:] += mono[:tail]

    fs.delete()
    return buf


# ─────────────────────────────────────────────────────────────────────────────
# Soundscape synthesis — parameterized for multi-poem use
# ─────────────────────────────────────────────────────────────────────────────
def make_soundscape(
    grid: TimeGrid,
    duration_sec: float,
    personality: dict,
    char: dict,
    route_ctx: dict,
    rng_seed: int = 42,
    layer8_mode: str = "arp",
) -> np.ndarray:
    n   = grid.samples(duration_sec)
    t   = np.linspace(0, duration_sec, n, endpoint=False)
    rng = np.random.default_rng(rng_seed)

    loyalty    = personality.get("loyalty_to_canon", 0.5)
    rebellious = personality.get("rebellious_mode")
    mode       = personality.get("route_mode", "bus")
    tod        = route_ctx.get("time_of_day", "afternoon")
    alignment  = char.get("alignment", "neutral").lower()
    quirks     = char.get("quirks", [])
    prefs      = personality.get("sound_preferences", {})
    themes     = personality.get("theme_affinities", {})
    syncopation = prefs.get("syncopation", 0.0)
    chaotic    = "chaotic" in alignment

    brightness = {"morning_rush": 1.0, "afternoon": 0.7, "evening_rush": 0.45,
                  "late_night": 0.15, "unknown": 0.55}.get(tod, 0.55)
    darkness_score = themes.get("darkness", 0.0)
    bass_weight    = (0.80 + (1.0 - brightness) * 0.55
                      + darkness_score * 0.25 + (1.0 - loyalty) * 0.20)

    base_hz   = 80 + loyalty * 80
    ST        = 2 ** (1 / 12)
    meas_samp = grid.samples(grid.measure_sec)

    CHORD_TYPES = {
        "major": [0,4,7], "minor": [0,3,7], "maj7": [0,4,7,11],
        "min7":  [0,3,7,10], "dom7": [0,4,7,10], "sus4": [0,5,7],
        "dim":   [0,3,6],    "aug":  [0,4,8],
    }
    PROGRESSIONS = {
        "resolved":   [(0,"maj7"),  (5,"maj7"),  (7,"dom7"),  (0,"maj7") ],
        "wandering":  [(0,"min7"),  (3,"major"), (5,"min7"),  (10,"dom7")],
        "dark":       [(0,"minor"), (8,"major"), (5,"minor"), (7,"dom7") ],
        "rebellious": [(0,"dom7"),  (6,"dom7"),  (1,"aug"),   (5,"dim")  ],
    }
    if rebellious == "invert":
        prog_key = "rebellious"
    elif loyalty < 0.4:
        prog_key = "dark"
    elif loyalty < 0.65:
        prog_key = "wandering"
    else:
        prog_key = "resolved"
    progression    = PROGRESSIONS[prog_key]
    CHORD_MEASURES = 2
    chord_samp     = grid.samples(grid.measures(CHORD_MEASURES))
    total_chords   = max(len(progression), int(np.ceil(n / chord_samp)))

    def euclidean_rhythm(k, n_steps):
        return [1 if (i * k) % n_steps < k else 0 for i in range(n_steps)]
    EUCLIDEAN_MAP = {3:(6,2), 4:(8,3), 6:(6,3), 5:(10,3), 7:(7,3)}
    n_slots, k_beats = EUCLIDEAN_MAP.get(grid.beats_per_measure, (8,3))
    euclid_pat = euclidean_rhythm(k_beats, n_slots)
    slot_samp  = max(1, int(meas_samp / n_slots))

    # — LAYER 1: Sub-bass drone —
    bass_root_hz = base_hz / 2
    if mode == "train":
        drone = sum((1.0/k)*np.sin(2*np.pi*bass_root_hz*k*t) for k in range(1,5))
    else:
        drone  = 1.00 * np.sin(2*np.pi*bass_root_hz*t)
        drone += 0.40 * brightness * np.sin(2*np.pi*bass_root_hz*2*t)
        drone += 0.20 * brightness * np.sin(2*np.pi*bass_root_hz*3*t)
    breath_rate = 1 / grid.measures(2)
    drone      *= 0.82 + 0.18 * np.sin(2*np.pi*breath_rate*t)
    drone       = drone / (np.abs(drone).max()+1e-9) * (0.22 * bass_weight)

    # — LAYER 2: Chord pad —
    pad          = np.zeros(n)
    attack_samp  = grid.samples(grid.beats(1.5))
    release_samp = grid.samples(grid.beats(1.0))
    for ci in range(total_chords):
        root_semi, ctype = progression[ci % len(progression)]
        cs = ci * chord_samp
        ce = min(cs + chord_samp, n)
        if cs >= n: break
        dur = ce - cs
        t_c = t[cs:ce]
        atk = min(attack_samp,  dur//3)
        rel = min(release_samp, dur//4)
        sus = max(0, dur - atk - rel)
        env = np.concatenate([np.linspace(0,1,atk), np.ones(sus), np.linspace(1,0,rel)])[:dur]
        chord_signal = np.zeros(dur)
        for interval in CHORD_TYPES[ctype]:
            hz = base_hz * (ST ** (root_semi + interval))
            chord_signal += 0.50 * np.sin(2*np.pi*hz*t_c)
            chord_signal += 0.25 * np.sin(2*np.pi*hz*1.0025*t_c)
            chord_signal += 0.25 * np.sin(2*np.pi*hz*0.9975*t_c)
        n_notes = len(CHORD_TYPES[ctype])
        pad[cs:ce] += chord_signal / (n_notes+1e-9) * env * 0.85 * (0.6+0.4*brightness)
    lp_sos = sp_signal.butter(2, 1400, btype="lowpass", fs=SAMPLE_RATE, output="sos")
    pad    = sp_signal.sosfilt(lp_sos, pad)
    pad    = pad / (np.abs(pad).max()+1e-9) * 0.34

    # — LAYER 3: SF2 acoustic bass —
    note_dur_sec = grid.beat_sec
    bass_events  = []
    BASS_PATTERNS = {
        3:[(0,1.00),(2,0.58)], 4:[(0,1.00),(2,0.62)],
        6:[(0,1.00),(3,0.58)], 5:[(0,1.00)],         7:[(0,1.00)],
    }
    bass_pattern  = BASS_PATTERNS.get(grid.beats_per_measure, [(0,1.00)])
    note_dur_samp = grid.samples(note_dur_sec)
    m_i = 0
    while m_i + note_dur_samp < n:
        chord_idx    = m_i // chord_samp
        root_semi, _ = progression[chord_idx % len(progression)]
        bass_hz      = (base_hz/2) * (ST**root_semi)
        midi_note    = hz_to_midi(bass_hz)
        for beat_offset, vol in bass_pattern:
            pos = m_i + int(beat_offset * grid.samples(grid.beat_sec))
            if syncopation > 0.4 and rng.random() < syncopation*0.3:
                pos += int(grid.samples(grid.beat_sec)*0.5*rng.choice([-1,1]))
            pos = max(0, min(n - note_dur_samp, pos))
            slot_in_meas = (pos - m_i) // slot_samp if slot_samp > 0 else 0
            if slot_in_meas < len(euclid_pat) and euclid_pat[slot_in_meas]:
                vol *= 0.30
            velocity = max(1, min(127, int(30 + vol*80)))
            bass_events.append((pos/SAMPLE_RATE, note_dur_sec, midi_note, velocity))
        m_i += meas_samp
    bass = render_sf2_layer(SF2_PATH, bass_events, n, GM_BASS_ACOUSTIC)
    lp_bass = sp_signal.butter(2, 600, btype="lowpass", fs=SAMPLE_RATE, output="sos")
    bass    = sp_signal.sosfilt(lp_bass, bass)
    bass    = bass / (np.abs(bass).max()+1e-9) * (0.58 * bass_weight)

    # — LAYER 4: Ambient texture —
    noise    = rng.normal(0, 1, n)
    sweep_lo = 300 + brightness*200
    sweep_hi = 900 + brightness*1400
    sweep    = sweep_lo + (sweep_hi-sweep_lo)*(0.5-0.5*np.cos(np.pi*t/duration_sec))
    chunk_sz = SAMPLE_RATE
    texture  = np.zeros(n)
    for i in range(0, n, chunk_sz):
        mid_freq = float(np.mean(sweep[i:i+chunk_sz]))
        lo = max(20.0, mid_freq*0.5)
        hi = min(SAMPLE_RATE/2-1, mid_freq*2.0)
        if hi <= lo: hi = lo+50
        sos = sp_signal.butter(2, [lo,hi], btype="bandpass", fs=SAMPLE_RATE, output="sos")
        end = min(i+chunk_sz, n)
        texture[i:end] = sp_signal.sosfilt(sos, noise[i:end])
    texture  = texture / (np.abs(texture).max()+1e-9)
    texture *= (themes.get("urban_life",0.5)*0.05 + themes.get("darkness",0.0)*0.07 + 0.018)

    # — LAYER 5: Euclidean heartbeat —
    def heart_tone(freq_hz, dur_samp, amp):
        t_loc  = np.arange(dur_samp) / SAMPLE_RATE
        t_norm = np.linspace(-2.0, 2.0, dur_samp)
        env    = np.exp(-t_norm**2 / 2.0)
        ht     = (np.sin(2*np.pi*freq_hz*t_loc)
                  + 0.30*np.sin(2*np.pi*freq_hz*2*t_loc))
        ht    /= np.abs(ht).max()+1e-9
        return amp * env * ht

    lub_samp   = grid.samples(0.11)
    dub_samp   = grid.samples(0.08)
    dub_offset = grid.samples(0.20)
    lub = heart_tone(65.0, lub_samp, 1.00)
    dub = heart_tone(50.0, dub_samp, 0.60)
    pulse   = np.zeros(n)
    m_start = 0
    while m_start < n:
        for si, active in enumerate(euclid_pat):
            if not active: continue
            pos = m_start + si * slot_samp
            if pos >= n: break
            end = min(pos+lub_samp, n)
            pulse[pos:end] += lub[:end-pos]
            dp = pos + dub_offset
            if dp < n:
                end = min(dp+dub_samp, n)
                pulse[dp:end] += dub[:end-dp]
        m_start += meas_samp
    ir_len = grid.samples(0.18)
    ir     = np.zeros(ir_len)
    for er_ms, er_g in [(0.010,0.50),(0.022,0.28),(0.040,0.14)]:
        ir[min(ir_len-1, int(er_ms*SAMPLE_RATE))] = er_g
    tail_s = int(0.05*SAMPLE_RATE)
    if tail_s < ir_len:
        tl = ir_len - tail_s
        ir[tail_s:] += rng.normal(0,1,tl)*np.exp(-np.linspace(0,5,tl))*0.04
    ir /= np.abs(ir).max()+1e-9
    pulse_wet  = sp_signal.fftconvolve(pulse, ir)[:n]
    pulse_wet /= np.abs(pulse_wet).max()+1e-9
    pulse      = pulse + 0.35*pulse_wet
    pulse     /= np.abs(pulse).max()+1e-9
    pulse     *= (0.88 * bass_weight)

    # — LAYER 6: Movement events —
    movement       = np.zeros(n)
    event_interval = grid.samples(grid.measures(8))
    event_dur_samp = grid.samples(grid.measures(2))
    ev_t           = np.linspace(0, grid.measures(2), event_dur_samp)
    ev_env         = np.concatenate([
        np.linspace(0, 1, event_dur_samp//3),
        np.linspace(1, 0, event_dur_samp - event_dur_samp//3),
    ])
    for i in range(event_interval, n-event_dur_samp, event_interval):
        glide_hz = base_hz*1.2*(1+0.08*np.sin(np.pi*ev_t/grid.measures(2)))
        ev_phase = 2*np.pi*np.cumsum(glide_hz)/SAMPLE_RATE
        movement[i:i+event_dur_samp] += ev_env * np.sin(ev_phase) * 0.05

    # — LAYER 7: Hum quirk —
    if "hums at stops" in quirks:
        hum_interval = grid.samples(grid.measures(4))
        hum_dur      = grid.samples(grid.measures(1))
        hum_t_local  = np.linspace(0, grid.measures(1), hum_dur)
        hum_env_loc  = np.concatenate([
            np.linspace(0,1,hum_dur//4), np.ones(hum_dur//2),
            np.linspace(1,0,hum_dur - hum_dur//4 - hum_dur//2),
        ])
        hum_tone = np.sin(2*np.pi*base_hz*1.5*hum_t_local)*hum_env_loc*0.07
        for i in range(0, n-hum_dur, hum_interval):
            drone[i:i+hum_dur] += hum_tone

    # — LAYER 8: Selectable high layer — "arp" | "pad" | "strings" ——————————
    if layer8_mode == "pad":
        # ── SHIMMER PAD: detuned sines, LFO tremolo, slow attack ─────────────
        lfo_rate = 0.20 + 0.15 * brightness
        atk_hi   = min(grid.samples(grid.beats(6.0)), n // 4)
        rel_hi   = min(grid.samples(grid.beats(4.0)), n // 5)
        pad_hi   = np.zeros(n)
        for ci in range(total_chords):
            root_semi, ctype = progression[ci % len(progression)]
            cs = ci * chord_samp
            ce = min(cs + chord_samp, n)
            if cs >= n:
                break
            dur = ce - cs
            t_c = t[cs:ce]
            atk = min(atk_hi, dur // 3)
            rel = min(rel_hi, dur // 4)
            sus = max(0, dur - atk - rel)
            env = np.concatenate([np.linspace(0., 1., atk),
                                   np.ones(sus),
                                   np.linspace(1., 0., rel)])[:dur]
            lfo = 0.72 + 0.28 * np.sin(2 * np.pi * lfo_rate * t_c)
            chord_sig = np.zeros(dur)
            for interval in CHORD_TYPES[ctype]:
                hz = base_hz * 4.0 * (ST ** (root_semi + interval))
                chord_sig += 0.35 * np.sin(2*np.pi * hz          * t_c)  # fundamental
                chord_sig += 0.25 * np.sin(2*np.pi * hz * 1.0041 * t_c)  # +7 cents
                chord_sig += 0.25 * np.sin(2*np.pi * hz * 0.9959 * t_c)  # −7 cents
                chord_sig += 0.15 * np.sin(2*np.pi * hz * 2.0    * t_c)  # octave shimmer
            n_notes = len(CHORD_TYPES[ctype])
            pad_hi[cs:ce] += (chord_sig / (n_notes + 1e-9)) * env * lfo
        hp_sos2 = sp_signal.butter(2, 800,   btype="highpass", fs=SAMPLE_RATE, output="sos")
        lp_sos2 = sp_signal.butter(2, 12000, btype="lowpass",  fs=SAMPLE_RATE, output="sos")
        pad_hi  = sp_signal.sosfilt(hp_sos2, pad_hi)
        pad_hi  = sp_signal.sosfilt(lp_sos2, pad_hi)
        layer8  = pad_hi / (np.abs(pad_hi).max() + 1e-9) * (0.20 + brightness * 0.07)

    elif layer8_mode == "strings":
        # ── STRUMMED STRINGS: SF2 steel guitar strum + string ensemble sustain ─
        STRUM_SPREAD_SEC = 0.018
        STRUM_HOLD_SEC   = grid.beat_sec
        STRUM_REGISTER   = 2.0
        STRUM_VEL_BASE   = 72
        STRUM_VEL_HALF   = 52
        strum_events = []
        for ci in range(total_chords):
            rs, ct = progression[ci % len(progression)]
            cs = ci * chord_samp
            if cs >= n:
                break
            strum_notes = [rs] + [rs + iv for iv in CHORD_TYPES[ct]]
            for strum_pos, vel in [(cs, STRUM_VEL_BASE),
                                    (cs + chord_samp // 2, STRUM_VEL_HALF)]:
                if strum_pos >= n:
                    break
                for si, interval in enumerate(strum_notes):
                    t_start = strum_pos / SAMPLE_RATE + si * STRUM_SPREAD_SEC
                    hz      = base_hz * STRUM_REGISTER * (ST ** interval)
                    note    = hz_to_midi(hz)
                    strum_events.append((t_start, STRUM_HOLD_SEC, note,
                                         max(1, min(127, vel - si * 4))))
        strum    = render_sf2_layer(SF2_PATH, strum_events, n, GM_STEEL_GUITAR)
        bp_strum = sp_signal.butter(2, [200.0, 9000.0], btype="bandpass",
                                     fs=SAMPLE_RATE, output="sos")
        strum    = sp_signal.sosfilt(bp_strum, strum)
        strum    = strum / (np.abs(strum).max() + 1e-9) * (0.22 + brightness * 0.06)
        SUSTAIN_VEL      = 38
        SUSTAIN_REGISTER = 1.0
        sustain_events = []
        for ci in range(total_chords):
            rs, ct = progression[ci % len(progression)]
            cs = ci * chord_samp
            ce = min(cs + chord_samp, n)
            if cs >= n:
                break
            dur_sec = (ce - cs) / SAMPLE_RATE
            for interval in CHORD_TYPES[ct][:2]:
                hz   = base_hz * SUSTAIN_REGISTER * (ST ** (rs + interval))
                note = hz_to_midi(hz)
                sustain_events.append((cs / SAMPLE_RATE, dur_sec, note, SUSTAIN_VEL))
        sustain  = render_sf2_layer(SF2_PATH, sustain_events, n, GM_STRINGS, gain=0.4)
        lp_sus   = sp_signal.butter(2, 4000, btype="lowpass", fs=SAMPLE_RATE, output="sos")
        sustain  = sp_signal.sosfilt(lp_sus, sustain)
        sustain  = sustain / (np.abs(sustain).max() + 1e-9) * (0.18 + brightness * 0.05)
        layer8   = strum + sustain

    else:
        # ── ARP (default): SF2 vibraphone / marimba — Euclidean cross-rhythm ──
        char_tone  = char.get("tone", "neutral").lower()
        use_vibe   = ("dreamy" in char_tone) or (loyalty >= 0.5)
        gm_prog    = GM_VIBRAPHONE if use_vibe else GM_MARIMBA
        note_decay = 0.80 if use_vibe else 0.22
        arp_n_slots   = n_slots * 2
        arp_slot_samp = max(1, meas_samp // arp_n_slots)
        avoid         = {k_beats, k_beats * 2, arp_n_slots - k_beats}
        arp_k_opts    = [k for k in range(3, arp_n_slots - 1) if k not in avoid]
        if not arp_k_opts:
            arp_k_opts = [max(3, arp_n_slots // 3)]
        arp_k      = int(rng.choice(arp_k_opts))
        arp_euclid = euclidean_rhythm(arp_k, arp_n_slots)
        base_octave    = int(rng.choice([3, 4, 4, 5]))
        oct_shift_prob = 0.25 + float(rng.random()) * 0.45
        arp_events  = []
        note_cursor = 0
        m_start_arp = 0
        measure_num = 0
        while m_start_arp < n:
            chord_idx        = m_start_arp // chord_samp
            root_semi, ctype = progression[chord_idx % len(progression)]
            intervals        = CHORD_TYPES[ctype]
            if rebellious == "invert":
                note_seq = list(reversed(intervals))
            elif chaotic:
                note_seq = list(rng.choice(intervals, size=len(intervals), replace=True))
            elif measure_num % 8 < 4:
                note_seq = intervals
            else:
                note_seq = list(reversed(intervals))
            for si, active in enumerate(arp_euclid):
                if not active:
                    continue
                pos = m_start_arp + si * arp_slot_samp
                if pos >= n:
                    break
                interval = note_seq[note_cursor % len(note_seq)]
                note_cursor += 1
                oct = base_octave
                if si % 2 == 1 and rng.random() < oct_shift_prob:
                    oct += 1
                note_hz   = base_hz * (2.0 ** (oct - 2)) * (ST ** (root_semi + interval))
                midi_note = hz_to_midi(note_hz)
                if si == 0:
                    vel_base = 80
                elif si == arp_n_slots // 2:
                    vel_base = 55
                elif si % 2 == 0:
                    vel_base = 42
                else:
                    vel_base = 30
                velocity = max(1, min(127, vel_base + int(rng.integers(-8, 9))))
                arp_events.append((pos / SAMPLE_RATE, note_decay, midi_note, velocity))
            m_start_arp += meas_samp
            measure_num += 1
        arp     = render_sf2_layer(SF2_PATH, arp_events, n, gm_prog)
        bp_lo, bp_hi = (600.0, 8000.0) if use_vibe else (400.0, 6000.0)
        bp_sos  = sp_signal.butter(2, [bp_lo, bp_hi], btype="bandpass",
                                    fs=SAMPLE_RATE, output="sos")
        arp     = sp_signal.sosfilt(bp_sos, arp)
        layer8  = arp / (np.abs(arp).max() + 1e-9) * (0.28 + brightness * 0.08)

    # — Mix —
    mix = drone + pad + bass + texture + pulse + movement + layer8
    fi  = grid.samples(grid.measures(2))
    fo  = grid.samples(grid.measures(4))
    if n > fi + fo:
        env = np.concatenate([np.linspace(0,1,fi), np.ones(n-fi-fo), np.linspace(1,0,fo)])
    else:
        env = np.ones(n)
    mix *= env
    return (mix / (np.abs(mix).max()+1e-9)).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def ndarray_to_segment(arr: np.ndarray) -> AudioSegment:
    pcm = (arr * 32767).astype(np.int16)
    return AudioSegment(
        pcm.tobytes(), frame_rate=SAMPLE_RATE, sample_width=2, channels=1
    ).set_channels(2)


def split_poem(text: str, lines_per_group: int = 1) -> list[tuple[str, bool]]:
    raw_stanzas = re.split(r"\n\s*\n", text.strip())
    raw_stanzas = [s.strip() for s in raw_stanzas if s.strip()]
    segments: list[tuple[str, bool]] = []
    for si, stanza in enumerate(raw_stanzas):
        lines  = [l.rstrip() for l in stanza.splitlines() if l.strip()]
        groups = [lines[i:i+lines_per_group] for i in range(0, len(lines), lines_per_group)]
        for gi, grp in enumerate(groups):
            long_pause = (gi == len(groups)-1) and (si < len(raw_stanzas)-1)
            segments.append(("\n".join(grp), long_pause))
    return segments


def tts_segment(client: OpenAI, text: str, voice: str) -> AudioSegment:
    resp = client.audio.speech.create(
        model=TTS_MODEL, voice=voice, input=text, speed=TTS_SPEED
    )
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    seg = AudioSegment.from_mp3(tmp)
    os.unlink(tmp)
    return seg


def build_poem_segment(
    poem: dict,
    personality: dict,
    char: dict,
    voice: str,
    client: OpenAI,
    label: str = "",
    route_name: str = "",
) -> AudioSegment:
    """Build the full mixed AudioSegment for one poem."""
    poem_text = poem.get("text", "")
    poem_meta = poem.get("metadata", {})
    route_ctx = poem_meta.get("context", {})
    route_id  = poem.get("route_id", "?")
    poem_id   = poem.get("id", route_id)

    # Deterministic rng seed from unique poem ID so each poem has its own soundscape
    rng_seed  = int(hashlib.md5(str(poem_id).encode()).hexdigest(), 16) % (2**31)
    poem_rng  = np.random.default_rng(rng_seed)

    # Per-poem BPM jitter: ±15 BPM from the time-of-day base so tempos feel distinct
    tod  = route_ctx.get("time_of_day", "afternoon")
    grid = get_time_grid(personality, char, tod)
    bpm_jitter = int(poem_rng.integers(-15, 16))
    grid = TimeGrid(bpm=max(30, grid.bpm + bpm_jitter),
                    beats_per_measure=grid.beats_per_measure,
                    beat_unit=grid.beat_unit)

    # Pre-process text: punct → line breaks
    poem_proc = re.sub(r'[,\u2014\u2013;:.]', '\n', poem_text)
    poem_proc = re.sub(r'\n{3,}', '\n\n', poem_proc)
    poem_proc = re.sub(r'[ \t]+', ' ', poem_proc).strip()

    segments = split_poem(poem_proc, lines_per_group=1)

    # Build spoken header: title + route name
    raw_title = poem.get("title", "").split("\n")[0].strip()
    is_timestamp = bool(re.match(r'^MARTA_\w+ - \d{4}', raw_title))
    clean_title = None if (not raw_title or is_timestamp) else raw_title
    rid = poem.get("route_id", route_id)
    display_route = route_name if (route_name and route_name != rid) else None

    if clean_title and display_route:
        header_text = f"{clean_title}. From {display_route}."
    elif clean_title:
        header_text = f"{clean_title}."
    elif display_route:
        header_text = f"From {display_route}."
    else:
        header_text = None

    header_clip = None
    if header_text:
        print(f'    🎤  {label} Header: "{header_text}"')
        header_clip = tts_segment(client, header_text, voice)

    # TTS
    clips = []
    for i, (seg_text, _) in enumerate(segments):
        seg_text = seg_text.strip()
        if not seg_text:
            continue
        print(f"    🎙  {label} TTS {i+1}/{len(segments)} ({len(seg_text.split())} words)…")
        clips.append(tts_segment(client, seg_text, voice))

    # Timing
    narr_sec = sum(len(c)/1000 for c in clips)
    gaps_sec = sum(
        grid.measures(STANZA_PAUSE_MEAS if is_stanza else LINE_PAUSE_MEAS)
        for _, is_stanza in segments[:-1]
    )
    total_sec = (grid.measures(INTRO_MEAS) + narr_sec
                 + gaps_sec + grid.measures(OUTRO_MEAS))

    # layer8_mode: poem-level override → route personality → default "arp"
    layer8_mode = poem.get("layer8_mode") or personality.get("layer8_mode", "arp")
    print(f"    🎵  Synthesizing soundscape ({total_sec:.0f}s) [layer8={layer8_mode}]…")
    sc_arr    = make_soundscape(grid, total_sec, personality, char, route_ctx, rng_seed,
                                layer8_mode=layer8_mode)
    soundscape = ndarray_to_segment(sc_arr)

    # Assemble narration track
    narration = AudioSegment.silent(duration=grid.measures_ms(INTRO_MEAS))
    if header_clip:
        # Overlay title/route announcement over the opening intro measures
        narration = narration.overlay(header_clip, position=0)
    for i, (clip, (_, is_stanza)) in enumerate(zip(clips, segments)):
        narration += clip
        if i < len(clips)-1:
            pause_m = STANZA_PAUSE_MEAS if is_stanza else LINE_PAUSE_MEAS
            narration += AudioSegment.silent(duration=grid.measures_ms(pause_m))
    narration += AudioSegment.silent(duration=grid.measures_ms(OUTRO_MEAS))

    if len(soundscape) < len(narration):
        soundscape += AudioSegment.silent(duration=len(narration)-len(soundscape))
    soundscape = soundscape[:len(narration)]

    final = normalize((soundscape - 9).overlay(narration))
    return final


def robotize(seg: AudioSegment) -> AudioSegment:
    """
    Make a TTS clip sound robotic via two stages:
      1. Ring modulation — multiply the waveform by a sine carrier.
         Introduces sum/difference sidebands that destroy natural formants.
      2. Bitcrushing — quantise to ROBOT_BITDEPTH bits, adding gritty aliasing.
    """
    sr   = seg.frame_rate
    pcm  = np.frombuffer(seg.raw_data, dtype=np.int16).astype(np.float32) / 32768.0

    # Handle stereo by processing each channel
    channels = seg.channels
    if channels == 2:
        left, right = pcm[0::2], pcm[1::2]
    else:
        left = pcm

    def process_mono(x):
        t_local = np.arange(len(x)) / sr
        # 1. Ring modulation — blend dry + ring-modded so words stay clear
        carrier  = np.sin(2 * np.pi * ROBOT_CARRIER_HZ * t_local)
        ring_mod = x * carrier
        x = (1.0 - ROBOT_RINGMOD_WET) * x + ROBOT_RINGMOD_WET * ring_mod
        # 2. Bit-crush — light quantisation for metallic texture
        levels = 2 ** ROBOT_BITDEPTH
        x = np.round(x * levels) / levels
        return x

    left = process_mono(left)
    if channels == 2:
        right = process_mono(right)
        interleaved = np.empty(len(left) + len(right), dtype=np.float32)
        interleaved[0::2] = left
        interleaved[1::2] = right
    else:
        interleaved = left

    # Normalise to avoid clipping after ring-mod amplitude changes
    peak = np.abs(interleaved).max()
    if peak > 0:
        interleaved = interleaved / peak * 0.92

    pcm_out = (interleaved * 32768.0).clip(-32768, 32767).astype(np.int16)
    return AudioSegment(
        pcm_out.tobytes(),
        frame_rate=sr,
        sample_width=2,
        channels=channels,
    )


def build_announcement(client: OpenAI, text: str = "") -> AudioSegment:
    """Generate the opening/closing statement with a robotic DSP voice."""
    print(f"  🤖  Generating robotic announcement…")
    body  = robotize(tts_segment(client, ANNOUNCEMENT_BODY,  ANNOUNCE_VOICE))
    close = robotize(tts_segment(client, ANNOUNCEMENT_CLOSE, ANNOUNCE_VOICE))
    return (AudioSegment.silent(duration=3000)
            + body
            + AudioSegment.silent(duration=ANNOUNCEMENT_PAUSE_MS)
            + close
            + AudioSegment.silent(duration=3000))


# ─────────────────────────────────────────────────────────────────────────────
# Main stream builder
# ─────────────────────────────────────────────────────────────────────────────
def build_stream(target_minutes: int = 60, seed: int | None = None):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("❌  OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)

    if not Path(SF2_PATH).exists():
        sys.exit(f"❌  SF2 not found: {SF2_PATH}")

    # ── Load data ──────────────────────────────────────────────────────────
    with open("data/poetry_graph.json") as f:
        graph = json.load(f)
    with open("data/route_personalities.json") as f:
        personalities = json.load(f)
    with open("data/character_profiles.json") as f:
        characters = json.load(f)

    all_poems = [
        nd for nd in graph["nodes"]
        if nd.get("type") == "poem"
        and nd.get("route_id", "").startswith("MARTA_")
        and len(nd.get("text", "").split()) >= MIN_POEM_WORDS
    ]

    # Keep only poems that have a real title AND a named route personality
    # (ensures every piece can be introduced properly on air)
    def _real_title(p):
        t = p.get("title", "").split("\n")[0].strip()
        return bool(t) and not re.match(r'^MARTA_\w+ - \d{4}', t)

    def _named_route(p):
        name = personalities.get(p.get("route_id", ""), {}).get("name", "")
        return bool(name) and name != p.get("route_id", "")

    all_poems = [p for p in all_poems if _real_title(p) and _named_route(p)]

    rng = np.random.default_rng(seed if seed is not None else int(time.time()))
    actual_seed = int(rng.integers(0, 2**31)) if seed is None else seed

    shuffled = list(rng.permutation(len(all_poems)))
    poem_order = [all_poems[i] for i in shuffled]

    target_sec  = target_minutes * 60
    # Reserve ~30s for both announcements
    budget_sec  = target_sec - 30
    max_sec     = target_sec + 300   # allow up to 5 min over

    print("=" * 58)
    print(f"  MARTA Poetry Audio Stream Generator")
    print(f"  Target  : {target_minutes} min  ({target_sec}s)")
    print(f"  Poems   : {len(poem_order)} available  (≥{MIN_POEM_WORDS} words)")
    print(f"  Seed    : {actual_seed}")
    print(f"  SF2     : {Path(SF2_PATH).name}")
    print("=" * 58)
    print()

    # ── Opening announcement ───────────────────────────────────────────────
    opening = build_announcement(client)
    elapsed_sec = len(opening) / 1000
    print(f"  Opening: {elapsed_sec:.0f}s\n")

    # ── Poem segments ──────────────────────────────────────────────────────
    segments: list[AudioSegment] = [opening]
    poem_count = 0

    for poem in poem_order:
        if elapsed_sec >= max_sec:
            break

        route_id    = poem.get("route_id", "")
        personality = personalities.get(route_id, {})
        char_key    = route_id.replace("MARTA_", "")
        char        = characters.get(char_key, characters.get(route_id, {}))
        route_name  = personality.get("name", route_id)

        # Random voice per poem (not derived from route — truly random each stream)
        voice = STREAM_VOICES[int(rng.integers(0, len(STREAM_VOICES)))]

        poem_count += 1
        print(f"[{poem_count}] {route_name}  ({route_id})  voice={voice}")

        try:
            seg = build_poem_segment(
                poem, personality, char, voice, client,
                label=f"[{poem_count}]",
                route_name=route_name,
            )
        except Exception as e:
            print(f"    ⚠️  Skipping — error: {e}")
            continue

        seg_sec = len(seg) / 1000
        elapsed_sec += seg_sec
        print(f"    ✓  {seg_sec:.0f}s  (stream total: {elapsed_sec:.0f}s / {target_sec}s)\n")
        segments.append(seg)

        if elapsed_sec >= budget_sec:
            print(f"  Budget reached after {poem_count} poems.\n")
            break

    # ── Concatenate (no crossfade — preserve title announcements) ───────────
    print("🔗  Concatenating segments…")
    stream = segments[0]
    for seg in segments[1:]:
        stream += seg

    # ── Export ─────────────────────────────────────────────────────────────
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"audio/stream_{ts}.mp3")
    output_path.parent.mkdir(exist_ok=True)

    print(f"💾  Exporting {len(stream)/1000:.0f}s → {output_path} …")
    stream.export(
        str(output_path),
        format="mp3",
        bitrate="192k",
        tags={
            "title":   "The MARTA Transit Poetry Project",
            "artist":  "ThoriumCat / MARTA Poetry",
            "album":   f"Stream {ts}",
            "comment": f"seed={actual_seed} poems={poem_count}",
        },
    )

    size_mb = output_path.stat().st_size / (1024*1024)
    print(f"\n✅  Stream saved: {output_path}")
    print(f"   Duration : {len(stream)/1000:.0f}s  ({len(stream)/1000/60:.1f} min)")
    print(f"   Poems    : {poem_count}")
    print(f"   Size     : {size_mb:.1f} MB")
    print(f"   Seed     : {actual_seed}")

    # ── Upload to blob storage (non-fatal) ──────────────────────────────────
    try:
        from stream_uploader import upload_stream
        result = upload_stream(
            output_path,
            metadata={
                "duration_sec": round(len(stream) / 1000),
                "poem_count":   poem_count,
                "seed":         actual_seed,
                "target_min":   target_minutes,
            },
        )
        if result["uploaded"]:
            print(f"\n📻  Live at: {result['url']}")
    except Exception as e:
        print(f"\n⚠️  Upload skipped: {e}")

    print(f"\nPlay: xdg-open {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MARTA Poetry Stream Generator")
    parser.add_argument("--duration", type=int, default=60,
                        help="Target stream duration in minutes (default: 60)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducible poem order")
    args = parser.parse_args()
    build_stream(target_minutes=args.duration, seed=args.seed)
