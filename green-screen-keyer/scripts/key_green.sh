#!/usr/bin/env bash
# Green screen keyer: ffmpeg colorkey + PIL edge cleanup
# Usage:
#   key_green.sh input.png output.png
#   key_green.sh input.png out/             # writes out/<basename>
#   key_green.sh input.png output.png --resize 240
#   key_green.sh input.png output.png --fix-stroke
#   key_green.sh input.png --detect-key-color

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEAN_PY="$SCRIPT_DIR/clean_edge.py"

if [ ! -f "$CLEAN_PY" ]; then
  echo "error: $CLEAN_PY not found" >&2
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "usage: $0 <input.png> [output.png] [--resize N] [--fix-stroke] [--detect-key-color]" >&2
  exit 1
fi

INPUT="$1"
shift

# Parse remaining args
RESIZE=0
FIX_STROKE=""
DETECT_ONLY=""
OUTPUT=""

for arg in "$@"; do
  case "$arg" in
    --resize)
      shift
      RESIZE="$1"
      shift
      ;;
    --fix-stroke)
      FIX_STROKE="--fix-stroke"
      shift
      ;;
    --detect-key-color)
      DETECT_ONLY="1"
      shift
      ;;
    *)
      OUTPUT="$arg"
      shift
      ;;
  esac
done

# Default output path
if [ -z "$OUTPUT" ]; then
  echo "usage: $0 <input.png> [output.png] [--resize N] [--fix-stroke]" >&2
  exit 1
fi

# If OUTPUT ends with /, treat as a directory
if [[ "$OUTPUT" == */ ]]; then
  mkdir -p "$OUTPUT"
  OUTPUT="${OUTPUT%/}/$(basename "$INPUT")"
fi

mkdir -p "$(dirname "$OUTPUT")"

# Auto-detect key color from the image's edge pixels
KEY_COLOR=$(python3 "$CLEAN_PY" "$INPUT" --detect-key-color 2>&1 | grep -oE '#[0-9A-Fa-f]{6}' | head -1)
if [ -z "$KEY_COLOR" ]; then
  echo "warn: could not auto-detect key color, falling back to #00B050" >&2
  KEY_COLOR="#00B050"
fi
echo "key color: $KEY_COLOR"

# Convert #RRGGBB to 0xRRGGBB for ffmpeg
HEX_KEY="0x${KEY_COLOR#\#}"

# Build ffmpeg filter
if [ "$RESIZE" -gt 0 ]; then
  FILTER="scale=${RESIZE}:${RESIZE}:flags=lanczos,colorkey=${HEX_KEY}:0.30:0.10"
else
  FILTER="colorkey=${HEX_KEY}:0.30:0.10"
fi

# Step 1: ffmpeg colorkey → temp file
TMP=$(mktemp -t green-key.XXXXXX).png
ffmpeg -y -i "$INPUT" -vf "$FILTER" -frames:v 1 -update 1 "$TMP" 2>/dev/null

# Step 2 + optional 3: PIL edge cleanup
if [ "$RESIZE" -gt 0 ]; then
  python3 "$CLEAN_PY" "$TMP" -o "$OUTPUT" --resize "$RESIZE" $FIX_STROKE
else
  python3 "$CLEAN_PY" "$TMP" -o "$OUTPUT" $FIX_STROKE
fi

rm -f "$TMP"
echo "done: $OUTPUT"
