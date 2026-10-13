#!/usr/bin/env bash
# Arab Store (Flask + static site/) — project start script.
# - Installs Python dependencies, builds dist/ from site/ (static deploy artifact),
#   writes deployment-output.json worker metadata, serves the Flask app in foreground.
# - Source and built output stay inside PROJECT_DIR; OPENCODE_WEB_DIR/RUNNER_TEMP
#   are used only for worker metadata (deployment-output.json) and logs.
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-3000}"
WEB_DIR="${OPENCODE_WEB_DIR:-/home/runner/work/_temp/omgithub-web}"

/usr/bin/time -p mkdir -p "$WEB_DIR"
/usr/bin/time -p python3 -m pip install --quiet -r requirements.txt
/usr/bin/time -p rm -rf dist
/usr/bin/time -p mkdir -p dist
/usr/bin/time -p cp -r site/. dist/
/usr/bin/time -p cp dist/store.html dist/index.html
/usr/bin/time -p python3 -m py_compile app.py lod.py
/usr/bin/time -p test -f dist/index.html
/usr/bin/time -p python3 - "$WEB_DIR" <<'PY'
import json, sys
web_dir = sys.argv[1]
with open(f"{web_dir}/deployment-output.json", "w", encoding="utf-8") as fh:
    json.dump({"project": "/home/runner/work/PlayGround/PlayGround",
               "directory": "/home/runner/work/PlayGround/PlayGround/dist"}, fh)
print(open(f"{web_dir}/deployment-output.json", encoding="utf-8").read())
PY

exec /usr/bin/time -p python3 app.py
