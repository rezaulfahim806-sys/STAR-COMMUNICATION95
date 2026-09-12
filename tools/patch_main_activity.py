from pathlib import Path
import re
p=Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
s=p.read_text(encoding='utf-8')
# Remove legacy Android-side Add Customer override.
s,n=re.subn(r'"var oldAdd=window\\.addCustomer;window\\.addCustomer=function\\(\\)\\{.*?;\\};"\\+\\n', '', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Legacy Add Customer override not found')
# Rename the injected dashboard card.
s=s.replace('Total Left Client', '＋ Add New Customer')
# Replace the injected inactive-filter navigation with the single Add Customer form.
pattern=r'onclick=\\+"?go\\(\\+\\\\\\x27customers\\+\\\\\\x27,\\{filter:\\\\\x27inactive\\\\\\x27\\}\\)\\+"?'
s,n=re.subn(pattern, 'onclick=\\"addCustomer()\\"', s, count=1)
# Remove dashboard Package block; package selection remains inside Customers > Add Customer.
s=s.replace('<div class=section><h3>📦 Package</h3><div class=kpi><span>Available Packages</span><b>20 Mb • 30 Mb • 40 Mb • 50 Mb</b></div></div>', '')
# Never show a manual status selector in the injected form.
s=s.replace('<select id=st class=select><option value=active>Active</option><option value=inactive>Inactive</option></select>', '<div class=detail><span>Initial Status</span><b class=success>ACTIVE (Automatic)</b></div>')
p.write_text(s,encoding='utf-8')
print('MainActivity patch applied; click replacements:', n)
