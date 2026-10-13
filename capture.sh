#!/usr/bin/env bash
# Capture desktop + mobile screenshots of the exact $CAPTURE_URL into $CAPTURE_DIR.
# - Exit 75: temporary navigation/browser infrastructure failures.
# - Exit 1: script usage errors or rendering defects (missing/empty screenshots).
# - Capture output stays outside the source tree; the app server is left running.
set -uo pipefail
cd "$(dirname "$0")"

if [[ -z "${CAPTURE_URL:-}" || -z "${CAPTURE_DIR:-}" ]]; then
  echo "capture.sh: Set CAPTURE_URL and CAPTURE_DIR." >&2
  exit 1
fi
RUNTIME="${RUNTIME_DIR:-/home/runner/work/_temp/omgithub-runtime}"

/usr/bin/time -p mkdir -p "$CAPTURE_DIR"
/usr/bin/time -p node "$RUNTIME/scripts/default-capture.mjs"
rc=$?
if [[ $rc -eq 75 ]]; then
  echo "capture.sh: transient browser/navigation failure (exit 75)." >&2
  exit 75
fi
if [[ $rc -ne 0 ]]; then
  echo "capture.sh: capture runtime failed (exit $rc)." >&2
  exit 1
fi
/usr/bin/time -p test -s "$CAPTURE_DIR/final-desktop.png"
/usr/bin/time -p test -s "$CAPTURE_DIR/final-mobile.png"
/usr/bin/time -p ls -la "$CAPTURE_DIR/final-desktop.png" "$CAPTURE_DIR/final-mobile.png"
echo "capture.sh: OK — $CAPTURE_URL captured to $CAPTURE_DIR"
