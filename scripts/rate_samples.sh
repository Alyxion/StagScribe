#!/bin/bash
# rate_samples.sh — Render all .stag samples, then rate them with Claude in 8 parallel processes.
#
# Usage:
#   ./scripts/rate_samples.sh              # rate all samples
#   ./scripts/rate_samples.sh nature_scenes # rate only one category
#   ./scripts/rate_samples.sh --rerender   # force re-render before rating
#
# Output:
#   tmp/ratings/<category>_<name>.json   — per-file JSON ratings
#   tmp/ratings/summary.txt              — aggregated summary sorted by score

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SAMPLES_DIR="samples"
RENDER_DIR="tmp/samples"
RATINGS_DIR="tmp/ratings"
PROMPT_FILE="tmp/rate_prompt.txt"
CATEGORY_FILTER="${1:-}"
RERENDER=false

if [[ "$CATEGORY_FILTER" == "--rerender" ]]; then
  RERENDER=true
  CATEGORY_FILTER="${2:-}"
fi

mkdir -p "$RENDER_DIR" "$RATINGS_DIR"

# Check prerequisites
if ! command -v claude &>/dev/null; then
  echo "Error: 'claude' CLI not found. Install Claude Code first." >&2
  exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Error: Prompt file not found at $PROMPT_FILE" >&2
  exit 1
fi

PROMPT=$(cat "$PROMPT_FILE")

# Collect work items: stag_path|png_path|key
WORK_FILE=$(mktemp)
trap "rm -f $WORK_FILE" EXIT

find "$SAMPLES_DIR" -name "*.stag" -type f | sort | while read -r stag; do
  category=$(basename "$(dirname "$stag")")
  name=$(basename "$stag" .stag)
  key="${category}_${name}"
  png="${RENDER_DIR}/${key}.png"

  # Optional category filter
  if [[ -n "$CATEGORY_FILTER" && "$category" != "$CATEGORY_FILTER" ]]; then
    continue
  fi

  # Render if missing or forced
  if [[ ! -f "$png" ]] || [[ "$RERENDER" == true ]]; then
    echo "Rendering $stag ..." >&2
    poetry run stagscribe render "$stag" -o "$png" 2>/dev/null || {
      echo "  FAILED to render $stag" >&2
      continue
    }
  fi

  echo "${stag}|${png}|${key}"
done > "$WORK_FILE"

TOTAL=$(wc -l < "$WORK_FILE" | tr -d ' ')
echo "Rating $TOTAL samples with 32 parallel Claude processes..."
echo ""

# Rate in parallel (8 processes)
rate_one() {
  local line="$1"
  IFS='|' read -r stag png key <<< "$line"
  local outfile="${RATINGS_DIR}/${key}.json"

  claude -p "$(cat <<EOF
$PROMPT

.stag source file path: $stag
Rendered PNG file path: $png

Read both files now and output your JSON rating.
EOF
)" --allowedTools "Read,Glob" > "$outfile" 2>/dev/null

  # Extract score for progress display
  local score
  score=$(grep -o '"score":[[:space:]]*[0-9]*' "$outfile" 2>/dev/null | head -1 | grep -o '[0-9]*$' || echo "?")
  echo "  [$score/10] $key"
}
export -f rate_one
export RATINGS_DIR PROMPT PROMPT_FILE

cat "$WORK_FILE" | xargs -P 32 -I {} bash -c 'rate_one "$@"' _ {}

echo ""
echo "=== Summary ==="
echo ""

# Build summary sorted by score (worst first)
{
  echo "Score | Sample | Summary"
  echo "------|--------|--------"
  for f in "$RATINGS_DIR"/*.json; do
    [[ -f "$f" ]] || continue
    key=$(basename "$f" .json)
    score=$(grep -o '"score":[[:space:]]*[0-9]*' "$f" 2>/dev/null | head -1 | grep -o '[0-9]*$' || echo "0")
    summary=$(grep -o '"summary":[[:space:]]*"[^"]*"' "$f" 2>/dev/null | head -1 | sed 's/"summary":[[:space:]]*"//;s/"$//' || echo "parse error")
    echo "$score | $key | $summary"
  done | sort -t'|' -k1 -n
} | tee "$RATINGS_DIR/summary.txt"

echo ""
echo "Detailed ratings: $RATINGS_DIR/*.json"
echo "Summary table:    $RATINGS_DIR/summary.txt"
