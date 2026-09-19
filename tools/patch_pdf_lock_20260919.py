from pathlib import Path
import re

# Final PDF guard: legacy build patches must never change the PDF layout.
j=Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
t=j.read_text(encoding="utf-8")

# Keep the approved native PDF layout at 25 customers per page.
t,n=re.subn(r'(final\\s+int\\s+W\\s*=\\s*842\\s*,\\s*H\\s*=\\s*595\\s*,\\s*PER_PAGE\\s*=\\s*)\\d+', r'\\g<1>25', t, count=1)
if n==0:
    raise SystemExit("Approved native PDF generator not found; refusing to alter PDF system.")

# Required approved PDF fields/layout markers.
required=[
    'CUSTOMER',
    'PPPoE USER',
    'PPPoE PASS',
    'ONU MAC',
    'PREV DUE',
    'RUNNING',
    'TOTAL DUE',
    'STATUS',
    'CONNECTION / EXPIRY'
]
for marker in required:
    if marker not in t:
        raise SystemExit("PDF guard failed: missing "+marker)

j.write_text(t,encoding="utf-8")
print("PDF LOCK OK: 25 customers/page; approved fields preserved")
