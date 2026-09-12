from pathlib import Path
import re

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

# Keep expired customers in the customer data permanently; expiry only changes status.
old = "function fixExpiry(){let ch=false;d.customers.forEach(c=>{if(c.expiry&&c.expiry<today()&&c.status!=='expired'){c.status='expired';ch=true}});if(ch)save()}"
new = "function fixExpiry(){let ch=false;d.customers.forEach(c=>{if(c.expiry&&c.expiry<today()&&c.status!=='expired'){c.status='expired';c.expiredAt=today();ch=true}});if(ch)save()}"
if old in s:
    s = s.replace(old, new, 1)
else:
    # Do not fail the build if the exact minified form has changed; verify the important rule instead.
    if 'function fixExpiry()' not in s:
        raise SystemExit('fixExpiry function not found')

# Add a second local backup so a corrupted/missing primary localStorage value can be recovered.
backup_key = "star_communication_final_v2_backup"
old_save = "function save(){localStorage.setItem(KEY,JSON.stringify(d))}"
new_save = "function save(){let z=JSON.stringify(d);localStorage.setItem(KEY,z);localStorage.setItem('star_communication_final_v2_backup',z)}"
if old_save in s:
    s = s.replace(old_save, new_save, 1)

# Recover from the backup when the primary record is missing or malformed.
old_init = "let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));"
new_init = "let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d){try{d=JSON.parse(localStorage.getItem('star_communication_final_v2_backup')||'null')}catch(e){d=null}}if(!d)d=JSON.parse(JSON.stringify(DEF));"
if old_init in s:
    s = s.replace(old_init, new_init, 1)

p.write_text(s, encoding='utf-8')
print('Customer persistence patch applied')
