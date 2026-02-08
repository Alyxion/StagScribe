#!/bin/bash
# render_samples.sh — Render .stag samples to PNG (16 parallel processes).
#
# Usage:
#   ./scripts/render_samples.sh                          # render all samples
#   ./scripts/render_samples.sh nature_scenes            # render one category
#   ./scripts/render_samples.sh nature_scenes/01_sunset  # render one file
#   ./scripts/render_samples.sh --clean                  # wipe tmp/samples then render all
#   ./scripts/render_samples.sh --debug labels,grid nature_scenes/01_sunset
#
# Output: tmp/samples/<category>_<name>.png

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SAMPLES_DIR="samples"
RENDER_DIR="tmp/samples"
PARALLEL=16
CLEAN=false
DEBUG_FLAG=""
FILTER=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean)
      CLEAN=true
      shift
      ;;
    --debug)
      if [[ $# -lt 2 ]]; then
        echo "Error: --debug requires a value (e.g. --debug all, --debug labels,grid)" >&2
        exit 1
      fi
      DEBUG_FLAG="$2"
      shift 2
      ;;
    -*)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--clean] [--debug MODE] [filter]" >&2
      exit 1
      ;;
    *)
      FILTER="$1"
      shift
      ;;
  esac
done

# Clean if requested
if [[ "$CLEAN" == true ]]; then
  echo "Cleaning $RENDER_DIR..."
  rm -rf "$RENDER_DIR"
fi

mkdir -p "$RENDER_DIR"

# Collect matching .stag files
find_stag_files() {
  if [[ -z "$FILTER" ]]; then
    find "$SAMPLES_DIR" -name "*.stag" -type f | sort
  elif [[ -f "$SAMPLES_DIR/${FILTER}.stag" ]]; then
    echo "$SAMPLES_DIR/${FILTER}.stag"
  elif [[ -d "$SAMPLES_DIR/$FILTER" ]]; then
    find "$SAMPLES_DIR/$FILTER" -name "*.stag" -type f | sort
  else
    find "$SAMPLES_DIR" -path "*${FILTER}*" -name "*.stag" -type f | sort
  fi
}

FILES=$(find_stag_files)
if [[ -z "$FILES" ]]; then
  echo "No .stag files found matching '$FILTER'" >&2
  exit 1
fi

TOTAL=$(echo "$FILES" | wc -l | tr -d ' ')

# Worker function — renders one .stag file
render_one() {
  local stag="$1"
  local category name key png
  category=$(basename "$(dirname "$stag")")
  name=$(basename "$stag" .stag)
  key="${category}_${name}"
  png="${RENDER_DIR}/${key}.png"

  local cmd=(poetry run stagscribe render "$stag" -o "$png")
  if [[ -n "$DEBUG_FLAG" ]]; then
    cmd+=(--debug "$DEBUG_FLAG")
  fi

  if "${cmd[@]}" 2>/dev/null; then
    echo "  ok  $key"
  else
    echo "  FAIL $key" >&2
    return 1
  fi
}
export -f render_one
export RENDER_DIR DEBUG_FLAG

echo "Rendering $TOTAL samples with $PARALLEL parallel processes..."

echo "$FILES" | xargs -P "$PARALLEL" -I {} bash -c 'render_one "$@"' _ {}

echo ""
echo "Done. Output: $RENDER_DIR/"
