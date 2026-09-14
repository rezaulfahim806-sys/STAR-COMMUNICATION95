from pathlib import Path
import re

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

# New customers always start Active; status is controlled automatically for new connections.
s2, n = re.subn(r'<select\s+[^>]*id=["\']st["\'][^>]*>.*?</select>', '<div class="detail"><span>Initial Status</span><b class="success">ACTIVE (Automatic)</b></div>', s, count=1, flags=re.S)
if n:
    s = s2
s = s.replace('status:st.value,createdAt:today()', "status:'active',createdAt:today()")

# FINAL BILLING RULE:
# - Expiry makes the customer Expired.
# - Any positive payment immediately makes the customer Active.
# - Payment is recorded in the current month.
# - Old previous due is reduced first; the unpaid part of the current monthly
#   bill is retained as previous due, so no amount disappears.
# Example: expired + monthly bill 500 + pay 400 => Active, Paid 400, Previous Due 100.
pattern = r'function savePayment\(id\)\{.*?\}\s*function details'
if re.search(pattern, s):
    new_func = "function savePayment(id){let amount=Number(amt.value||0);if(amount<=0){toast('Enter a valid payment');return}let c=d.customers.find(x=>String(x.id)===String(id));if(!c)return;let oldPrev=Math.max(0,Number(c.prevDue||0));let paidBefore=paid(c,month());d.payments.push({id:Date.now().toString(),customer:id,amount,date:today(),month:month(),status:'paid',source:'manual',ref:ref.value||''});let appliedPrev=Math.min(oldPrev,amount);let remainingAmount=Math.max(0,amount-appliedPrev);let currentDue=Math.max(0,Number(c.fee||0)-paidBefore-remainingAmount);c.prevDue=Math.max(0,oldPrev-appliedPrev)+currentDue;c.status='active';let x=new Date();x.setMonth(x.getMonth()+1,0);c.expiry=x.getFullYear()+'-'+pad(x.getMonth()+1)+'-'+pad(x.getDate());save();closeSheet();toast('Payment Saved — Customer Active — Due '+due(c));render()}function details"
    s = re.sub(pattern, new_func, s, count=1, flags=re.S)

p.write_text(s, encoding='utf-8')
print('Fixed: expired partial payment now reactivates and preserves the remaining due as previous due.')
