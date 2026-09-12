from pathlib import Path
import re

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

# The current Add Customer form is already a single-source form on Customers.
# If an older form is present, remove its manual status selector and force Active.
if 'New customers are automatically Active' not in s and 'Customer add is available only from this Customers page' not in s:
    pat = r"function addCustomer\(\)\{openSheet\(`<h3>Add Customer</h3>(.*?)<select id=\\\"st\\\" class=\\\"select\\\">.*?</select><button class=\\\"btn green full\\\" onclick=\\\"saveCustomer\(\)\\\">Save Customer</button>`\)\}"
    repl = r'''function addCustomer(){openSheet(`<h3>Add Customer</h3><div class="muted" style="margin-bottom:6px">New customers are automatically Active. Status will update automatically from expiry and bill payment.</div>\1<div class="detail"><span>Initial Status</span><b class="success">ACTIVE</b></div><button class="btn green full" onclick="saveCustomer()">Save Customer</button>`)}'''
    s, n = re.subn(pat, repl, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit('Could not update Add Customer form')

# Always force new customers to Active.
s = s.replace("status:st.value,createdAt:today()", "status:'active',createdAt:today()")

# Restore automatic reactivation after a fully paid expired bill.
m = re.search(r"function savePayment\(id\)\{.*?\}\s*function details", s)
if not m:
    raise SystemExit('Could not isolate savePayment function')
new_func = "function savePayment(id){let amount=Number(amt.value||0);if(amount<=0)return;let c=d.customers.find(x=>String(x.id)===String(id));if(!c)return;let beforeDue=due(c);d.payments.push({id:Date.now().toString(),customer:id,amount,date:today(),month:month(),status:'paid',source:'manual',ref:ref.value||''});let remaining=Math.max(0,beforeDue-amount);if(Number(c.prevDue||0)>0){c.prevDue=Math.max(0,Number(c.prevDue||0)-amount)}if(c.status==='expired'&&remaining<=0){c.status='active';let x=new Date();x.setMonth(x.getMonth()+1,0);c.expiry=x.getFullYear()+'-'+pad(x.getMonth()+1)+'-'+pad(x.getDate())}save();closeSheet();toast(remaining<=0?'Bill Paid — Customer Active':'Payment Saved');render()}function details"
s = s[:m.start()] + new_func + s[m.end():]

p.write_text(s, encoding='utf-8')
print('Customer add/status automation patch applied successfully.')