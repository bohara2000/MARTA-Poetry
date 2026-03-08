"""
Stream Uploader
===============
Uploads a generated stream MP3 to Azure Blob Storage under the "streams" container.

Writes two blobs every time:
  streams/current.mp3          — always overwritten; the active broadcast
  streams/archive/YYYYMMDD_HHMMSS.mp3 — permanent archive copy

Returns the public URL of current.mp3 (used by the radio endpoint and status API).

If blob storage is not configured the file stays local and the local path is returned.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from config import STORAGE_CONNECTION_STRING, STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY

STREAMS_CONTAINER = os.getenv("STREAMS_CONTAINER_NAME", "streams")
STREAM_META_BLOB  = "current.json"
STREAM_AUDIO_BLOB = "current.mp3"
SAS_EXPIRY_DAYS   = 365 * 2   # SAS URL valid for 2 years


def _get_blob_service():
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        return None

    if STORAGE_CONNECTION_STRING:
        try:
            return BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        except Exception as e:
            print(f"⚠️  stream_uploader: connection string failed ({e})")

    if STORAGE_ACCOUNT_NAME and STORAGE_ACCOUNT_KEY:
        try:
            from azure.core.credentials import AzureNamedKeyCredential
            cred = AzureNamedKeyCredential(STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY)
            return BlobServiceClient(
                account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
                credential=cred,
            )
        except Exception as e:
            print(f"⚠️  stream_uploader: account key failed ({e})")

    return None


def _ensure_container(blob_service) -> bool:
    """Create the streams container (private) if it doesn't exist."""
    try:
        cc = blob_service.get_container_client(STREAMS_CONTAINER)
        if not cc.exists():
            cc.create_container()   # private — no public_access
            print(f"✅  Created blob container '{STREAMS_CONTAINER}' (private)")
        return True
    except Exception as e:
        print(f"⚠️  stream_uploader: container setup failed ({e})")
        return False


def _make_sas_url(blob_service, blob_name: str) -> str:
    """Generate a read-only SAS URL for a blob, valid for SAS_EXPIRY_DAYS."""
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    account_name = (
        STORAGE_ACCOUNT_NAME
        or getattr(blob_service, "account_name", None)
        or "unknown"
    )
    account_key = STORAGE_ACCOUNT_KEY
    if not account_key:
        # Extract key from connection string if possible
        cs = STORAGE_CONNECTION_STRING or ""
        for part in cs.split(";"):
            if part.startswith("AccountKey="):
                account_key = part[len("AccountKey="):]
                break
    if not account_key:
        raise ValueError("Cannot generate SAS: no account key available")
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=STREAMS_CONTAINER,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(days=SAS_EXPIRY_DAYS),
    )
    return f"https://{account_name}.blob.core.windows.net/{STREAMS_CONTAINER}/{blob_name}?{sas_token}"


def upload_stream(mp3_path: str | Path, metadata: dict | None = None) -> dict:
    """
    Upload a stream MP3 to blob storage.

    Parameters
    ----------
    mp3_path : str | Path
        Absolute or relative path to the generated MP3 file.
    metadata : dict, optional
        Extra metadata to include in current.json (duration, poem count, seed, etc.)

    Returns
    -------
    dict with keys:
        url          – public URL of current.mp3 (blob) or local path fallback
        archive_url  – public URL of the archive copy (if blob upload succeeded)
        uploaded     – True if blob upload succeeded
        meta         – the metadata dict written to current.json
    """
    mp3_path = Path(mp3_path)
    if not mp3_path.exists():
        raise FileNotFoundError(f"stream_uploader: {mp3_path} not found")

    now = datetime.now(timezone.utc)
    ts  = now.strftime("%Y%m%d_%H%M%S")

    meta = {
        "generated_at": now.isoformat(),
        "filename":     mp3_path.name,
        "size_bytes":   mp3_path.stat().st_size,
        **(metadata or {}),
    }

    blob_service = _get_blob_service()
    if blob_service is None or not _ensure_container(blob_service):
        print("⚠️  stream_uploader: no blob storage — stream stays local")
        meta["url"] = str(mp3_path)
        return {"url": str(mp3_path), "archive_url": None, "uploaded": False, "meta": meta}

    from azure.storage.blob import ContentSettings
    mp3_settings = ContentSettings(content_type="audio/mpeg")
    json_settings = ContentSettings(content_type="application/json")
    archive_blob = f"archive/{ts}.mp3"

    data = mp3_path.read_bytes()
    account_name = (
        STORAGE_ACCOUNT_NAME
        or blob_service.account_name
        or "unknown"
    )
    base_url = f"https://{account_name}.blob.core.windows.net/{STREAMS_CONTAINER}"

    try:
        cc = blob_service.get_container_client(STREAMS_CONTAINER)

        # current.mp3 — overwrite
        cc.upload_blob(STREAM_AUDIO_BLOB, data, overwrite=True,
                       content_settings=mp3_settings)

        # archive copy
        cc.upload_blob(archive_blob, data, overwrite=True,
                       content_settings=mp3_settings)

        # Generate SAS URLs so the frontend/API can access private blobs
        current_url = _make_sas_url(blob_service, STREAM_AUDIO_BLOB)
        archive_url = _make_sas_url(blob_service, archive_blob)

        meta["url"]         = current_url
        meta["archive_url"] = archive_url

        # current.json sidecar — stores the SAS URL for the status endpoint
        cc.upload_blob(STREAM_META_BLOB,
                       json.dumps(meta, indent=2).encode(),
                       overwrite=True,
                       content_settings=json_settings)

        print(f"☁️   Uploaded → {STREAMS_CONTAINER}/current.mp3")
        print(f"☁️   Archive  → {STREAMS_CONTAINER}/{archive_blob}")
        return {"url": current_url, "archive_url": archive_url, "uploaded": True, "meta": meta}

    except Exception as e:
        print(f"⚠️  stream_uploader: upload failed ({e}) — stream stays local")
        meta["url"] = str(mp3_path)
        return {"url": str(mp3_path), "archive_url": None, "uploaded": False, "meta": meta}
