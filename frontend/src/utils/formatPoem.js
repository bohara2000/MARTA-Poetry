/**
 * formatForAudio — mirrors the punctuation→line-break preprocessing
 * used in demo_soundscape.py before passing text to TTS.
 *
 * Converts inline punctuation (commas, em-dashes, en-dashes, semicolons,
 * colons, periods) into newlines so each resulting phrase reads as its own
 * breath unit. Useful for previewing how a poem will be segmented for audio.
 */
export function formatForAudio(text) {
  if (!text) return text;
  return text
    .replace(/[,\u2014\u2013;:.]/g, '\n') // punct → line break
    .replace(/\n{3,}/g, '\n\n')            // collapse triple+ newlines
    .replace(/[ \t]+/g, ' ')               // collapse horizontal whitespace
    .trim();
}
