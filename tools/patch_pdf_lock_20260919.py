from pathlib import Path
import re

j=Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
t=j.read_text(encoding="utf-8")

# Final PDF guard: keep the approved native 25-customer layout.
pat=r'(final\s+int\s+W\s*=\s*842\s*,\s*H\s*=\s*595\s*,\s*PER_PAGE\s*=\s*)\d+'
t,n=re.subn(pat,r'\g<1>25',t,count=1)
if n==0:
    # The source is already approved; do not fail the build just because
    # whitespace/formatting differs from the guard pattern.
    if 'final int W=842,H=595,PER_PAGE=25;' not in t:
        raise SystemExit("Approved native PDF generator not found; refusing to alter PDF system.")

required=['CUSTOMER','PPPoE USER','PPPoE PASS','ONU MAC','PREV DUE','RUNNING','TOTAL DUE','STATUS','CONNECTION / EXPIRY']
for marker in required:
    if marker not in t:
        raise SystemExit("PDF guard failed: missing "+marker)

j.write_text(t,encoding="utf-8")
print("PDF LOCK OK: 25 customers/page; approved fields preserved")
