#!/bin/bash
# Data+ layout build: poster.html -> build/horn-ok-please-poster.pdf (this folder only)
set -e
cd "$(dirname "$0")"
CHROME=${CHROME:-google-chrome}
mkdir -p build
rm -f build/horn-ok-please-poster.pdf
timeout 60 "$CHROME" --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer --allow-file-access-from-files \
  --run-all-compositor-stages-before-draw --virtual-time-budget=5000 \
  --print-to-pdf=build/horn-ok-please-poster.pdf "file://$PWD/poster.html" 2>/dev/null || true
[ -s build/horn-ok-please-poster.pdf ] || { echo "no PDF" >&2; exit 1; }
timeout 60 "$CHROME" --headless=new --no-sandbox --disable-gpu --allow-file-access-from-files --window-size=2304,2304 --virtual-time-budget=5000 --dump-dom "file://$PWD/poster.html" 2>/dev/null | python3 -c "import sys,re,html;m=re.search(r'<pre id=\"measure\"[^>]*>(.*?)</pre>',sys.stdin.read(),re.S);print('\n'.join(l for l in html.unescape(m.group(1)).splitlines() if not l.startswith('EL\t')) if m else 'no measure')"
