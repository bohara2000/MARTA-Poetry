"""
MARTA Poetry — Azure Functions
================================
Timer-triggered function that regenerates the radio stream every 90 minutes
and uploads it to Azure Blob Storage so the radio endpoint always has fresh audio.

Deploy requirements (besides the normal backend deps):
    pip install azure-functions pydub pyfluidsynth openai python-dotenv numpy scipy \
                azure-storage-blob fluidsynth

App settings needed in the Function App:
    OPENAI_API_KEY
    STORAGE_CONNECTION_STRING  (or STORAGE_ACCOUNT_NAME + STORAGE_ACCOUNT_KEY)
    STREAMS_CONTAINER_NAME     (default: "streams")
    STREAM_DURATION_MIN        (default: "10")

The function runs sys.path magic to import stream_generator and stream_uploader
from the backend folder, which should be co-deployed alongside the function.
"""

import azure.functions as func
import logging
import os
import sys
from pathlib import Path

app = func.FunctionApp()

def _setup_backend_path():
    """Add the backend directory to sys.path so we can import our generator."""
    # When deployed, the backend/ folder should sit one level up from functions/
    here    = Path(__file__).parent
    backend = (here.parent / "backend").resolve()
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    # Also try the same directory (flat deploy layout)
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    # Change cwd so relative paths inside stream_generator (data/, audio/) work
    os.chdir(str(backend) if backend.exists() else str(here))


@app.timer_trigger(
    schedule="0 */90 * * * *",   # every 90 minutes
    arg_name="timer",
    run_on_startup=False,
    use_monitor=False,
)
def regenerate_stream(timer: func.TimerRequest) -> None:
    """
    Regenerate the MARTA Poetry radio stream and upload to blob storage.
    Runs every 90 minutes automatically.
    """
    if timer.past_due:
        logging.warning("Timer is past due — running anyway.")

    logging.info("🎙  MARTA Poetry stream regeneration starting…")

    _setup_backend_path()

    duration_min = int(os.getenv("STREAM_DURATION_MIN", "10"))

    try:
        from stream_generator import build_stream
        logging.info(f"Generating {duration_min}-minute stream…")
        build_stream(target_minutes=duration_min)
        logging.info("✅  Stream generation complete (upload handled inside build_stream).")

    except Exception as e:
        logging.error(f"❌  Stream generation failed: {e}", exc_info=True)
        raise   # re-raise so Functions marks the run as failed for alerting
