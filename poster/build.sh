#!/bin/bash
# Render poster.html to the 24x24 in PDF with headless Chrome, then print layout measurements.
set -e
cd "$(dirname "$0")"
CHROME=${CHROME:-google-chrome}
mkdir -p build
# Headless Chrome writes the PDF, then often stays running. timeout lets the script finish.
timeout 60 "$CHROME" --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
  --allow-file-access-from-files --run-all-compositor-stages-before-draw \
  --virtual-time-budget=5000 \
  --print-to-pdf=build/horn-ok-please-poster.pdf "file://$PWD/poster.html" 2>/dev/null || true
if [ ! -s build/horn-ok-please-poster.pdf ]; then
  echo "chrome did not write the poster PDF" >&2
  exit 1
fi
cp build/horn-ok-please-poster.pdf horn-ok-please.pdf
rm -f build/prev*.png; pdftoppm -r 60 -png build/horn-ok-please-poster.pdf build/prev_$(date +%s)
timeout 60 "$CHROME" --headless=new --no-sandbox --disable-gpu --allow-file-access-from-files \
  --window-size=2304,2304 --virtual-time-budget=5000 --dump-dom "file://$PWD/poster.html" 2>/dev/null \
  | python3 -c "import sys,re,html;m=re.search(r'<pre id=\"measure\"[^>]*>(.*?)</pre>',sys.stdin.read(),re.S);print('\n'.join(l for l in html.unescape(m.group(1)).splitlines() if not l.startswith('EL\t')) if m else 'no measure')"
