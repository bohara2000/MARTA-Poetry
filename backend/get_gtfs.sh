#!/bin/bash
# Download the latest MARTA GTFS feed and extract it to backend/data/gtfs/

set -e

DATA_DIR="$(dirname "$0")/data/gtfs"
GTFS_URL="https://itsmarta.com/google_transit_feed/google_transit.zip"
ZIP_FILE="$DATA_DIR/google_transit_feed.zip"

mkdir -p "$DATA_DIR"

# Download GTFS feed
curl -L "$GTFS_URL" -o "$ZIP_FILE"

# Unzip only GTFS files (routes.txt, stops.txt, etc.)
unzip -o "$ZIP_FILE" -d "$DATA_DIR"

# Optionally remove the zip file
echo "Cleaning up zip file..."
rm "$ZIP_FILE"

echo "GTFS files downloaded and extracted to $DATA_DIR."
