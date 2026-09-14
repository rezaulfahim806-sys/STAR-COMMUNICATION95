from pathlib import Path
import re

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

# Final rule: once a customer has any positive paid amount in the current month,
# expiry must not put them back into Expired. They remain Active until the next
# expiry date. This also fixes the Expired dashboard count/list after payment.
pattern = r'function fixExpiry\(\)\{.*?\}\s*function rollover'
replacement = "function fixExpiry(){let ch=false;d.customers.forEach(c=>{let paidNow=paid(c,month());if(paidNow>0){if(c.status!=='active'){c.status='active';ch=true}}else if(c.expiry&&c.expiry<today()&&c.status!=='expired'){c.status='expired';ch=true}});if(ch)save()}function rollover"

if re.search(pattern, s):
    s = re.sub(pattern, replacement, s, count=1, flags=re.S)
    print('Fixed: any positive current-month payment keeps customer Active and out of Expired.')
else:
    print('fixExpiry pattern not found; no change made')

p.write_text(s, encoding='utf-8')
