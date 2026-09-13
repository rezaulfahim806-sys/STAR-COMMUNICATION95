from pathlib import Path
import re

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

# New customers always start Active; remove manual status selection if present.
s2, n = re.subn(r'<select\s+[^>]*id=["\']st["\'][^>]*>.*?</select>', '<div class="detail"><span>Initial Status</span><b class="success">ACTIVE (Automatic)</b></div>', s, count=1, flags=re.S)
if n == 0:
    s2 = s
s = s2
s = s.replace('status:st.value,createdAt:today()', "status:'active',createdAt:today()")

# Expired customers stay Expired after partial payment. The payment reduces Due only.
m = re.search(r'function savePayment\(id\)\{.*?\}\s*function details', s)
if m:
    new_func = "function savePayment(id){let amount=Number(amt.value||0);if(amount<=0)return;let c=d.customers.find(x=>String(x.id)===String(id));if(!c)return;let beforeDue=Math.max(0,Number(due(c)||0));d.payments.push({id:Date.now().toString(),customer:id,amount,date:today(),month:month(),status:'paid',source:'manual',ref:ref.value||''});let remaining=Math.max(0,beforeDue-amount);let prev=Number(c.prevDue||0);if(prev>0){let applied=Math.min(prev,amount);c.prevDue=Math.max(0,prev-applied);}if(c.status!=='expired'&&amount>0){c.status='active';let x=new Date();x.setMonth(x.getMonth()+1,0);c.expiry=x.getFullYear()+'-'+pad(x.getMonth()+1)+'-'+pad(x.getDate());}save();closeSheet();toast(remaining>0?'Partial Payment Saved — Due '+remaining:(c.status==='expired'?'Payment Saved — Customer Still Expired':'Bill Paid — Customer Active'));render()}function details"
    s = s[:m.start()] + new_func + s[m.end():]

p.write_text(s, encoding='utf-8')
print('Expired partial-payment rule patched successfully.')
