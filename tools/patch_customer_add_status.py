from pathlib import Path
import re

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

# New customers always start Active; remove manual status selection if present.
s2, n = re.subn(r'<select\s+[^>]*id=[\"\']st[\"\'][^>]*>.*?</select>', '<div class="detail"><span>Initial Status</span><b class="success">ACTIVE (Automatic)</b></div>', s, count=1, flags=re.S)
if n == 0:
    # Do not fail the APK build if an earlier patch already removed the selector.
    s2 = s
s = s2
s = s.replace('status:st.value,createdAt:today()', "status:'active',createdAt:today()")

# Manual full payment reactivates an expired customer and extends expiry to month-end.
m = re.search(r'function savePayment\(id\)\{.*?\}\s*function details', s)
if m:
    new_func = "function savePayment(id){let amount=Number(amt.value||0);if(amount<=0)return;let c=d.customers.find(x=>String(x.id)===String(id));if(!c)return;let beforeDue=due(c);d.payments.push({id:Date.now().toString(),customer:id,amount,date:today(),month:month(),status:'paid',source:'manual',ref:ref.value||''});let remaining=Math.max(0,beforeDue-amount);if(Number(c.prevDue||0)>0)c.prevDue=Math.max(0,Number(c.prevDue||0)-amount);if(c.status==='expired'&&remaining<=0){c.status='active';let x=new Date();x.setMonth(x.getMonth()+1,0);c.expiry=x.getFullYear()+'-'+pad(x.getMonth()+1)+'-'+pad(x.getDate())}save();closeSheet();toast(remaining<=0?'Bill Paid — Customer Active':'Payment Saved');render()}function details"
    s = s[:m.start()] + new_func + s[m.end():]

p.write_text(s, encoding='utf-8')
print('Customer add/status automation patch applied successfully.')
