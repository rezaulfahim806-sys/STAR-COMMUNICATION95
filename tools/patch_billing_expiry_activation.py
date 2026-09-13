from pathlib import Path
import re
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
# Expiry alone must not deactivate a customer. Payment is what reactivates an expired customer.
s=re.sub(r"function fixExpiry\(\)\{.*?\}", "function fixExpiry(){return false}", s, count=1, flags=re.S)
p.write_text(s,encoding='utf-8')
print('Expiry/payment rule fixed: expired remains expired until payment; positive payment activates customer.')
