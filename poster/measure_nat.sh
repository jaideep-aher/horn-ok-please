#!/bin/bash
# natural (unstretched) heights of panels and inner columns, pt
cd "$(dirname "$0")"
sed 's#</style>#.row{align-items:flex-start!important}</style>#; s#o.push(.inner scrollH#document.querySelectorAll(".panel > div, .panel > section, .panel div[style*=flex-direction]").forEach(e=>{const r=e.getBoundingClientRect();o.push("  sub "+(e.className||e.getAttribute("style")||"").slice(0,40)+" h "+(r.height*0.75).toFixed(0))});o.push(\x27inner scrollH#' poster.html > /tmp/nat.html
cp /tmp/nat.html ./_nat.html
${CHROME:-google-chrome} --headless=new --no-sandbox --disable-gpu --allow-file-access-from-files --window-size=2304,2304 --virtual-time-budget=5000 --dump-dom file://$PWD/_nat.html 2>/dev/null | python3 -c "import sys,re,html;m=re.search(r'<pre id=\"measure\"[^>]*>(.*?)</pre>',sys.stdin.read(),re.S);print(html.unescape(m.group(1)) if m else 'no measure')"
rm -f _nat.html
