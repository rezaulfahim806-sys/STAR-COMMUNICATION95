from pathlib import Path
import re

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

# Keep customer data across app restarts, with a backup copy as an extra safeguard.
s=s.replace("let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));",
            "let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d){try{d=JSON.parse(localStorage.getItem(KEY+'_backup')||'null')}catch(e){d=null}}if(!d)d=JSON.parse(JSON.stringify(DEF));")
s=s.replace("function save(){localStorage.setItem(KEY,JSON.stringify(d))}",
            "function save(){let s=JSON.stringify(d);localStorage.setItem(KEY,s);try{localStorage.setItem(KEY+'_backup',s)}catch(e){}}")

# Make the in-app form compact instead of taking almost the entire screen.
s=s.replace('.modal.show{display:flex}.sheet{width:min(520px,100%);max-height:92vh;overflow:auto;background:#fff;border-radius:20px 20px 0 0;padding:15px}',
            '.modal.show{display:flex}.sheet{width:min(500px,100%);max-height:78vh;overflow:auto;background:#fff;border-radius:18px 18px 0 0;padding:12px}.sheet h3{font-size:18px;margin:2px 0 8px}.sheet .input,.sheet .select{padding:8px;margin:3px 0;font-size:13px}.sheet .btn{padding:9px 11px}')

# One customer-add location only; status is automatic.
new_add="""function addCustomer(){openSheet(`<h3>Add Customer</h3><div class="muted" style="margin-bottom:6px">Customer add is available only from this Customers page. New customers are automatically Active.</div><input id="n" class="input" placeholder="Customer name"><input id="p" class="input" placeholder="Mobile / WhatsApp"><input id="a" class="input" placeholder="Address"><label class="muted">Package</label><select id="pkg" class="select"><option value="20 Mb">20 Mb</option><option value="30 Mb" selected>30 Mb</option><option value="40 Mb">40 Mb</option><option value="50 Mb">50 Mb</option></select><input id="fee" class="input" type="number" placeholder="Monthly fee"><input id="pp" class="input" placeholder="PPPoE username"><input id="pw" class="input" placeholder="PPPoE password"><input id="onu" class="input" placeholder="ONU ID"><label class="muted">Connection Date</label><input id="cd" class="input" type="date" value="${today()}"><label class="muted">Expiry Date</label><input id="ex" class="input" type="date"><input id="prev" class="input" type="number" value="0" placeholder="Previous due"><div class="detail"><span>Initial Status</span><b class="success">ACTIVE (Automatic)</b></div><button class="btn green full" onclick="saveCustomer()">Save Customer</button>`)}"""
s, n = re.subn(r'function addCustomer\(\)\{openSheet\(`.*?`\)\}\s*function saveCustomer', new_add+'function saveCustomer', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Could not locate addCustomer function')

# Always create new customers as active.
s=re.sub(r"status:st\.value,createdAt:today\(\)", "status:'active',createdAt:today()", s)

# Full payment on an expired customer reactivates it and starts a fresh expiry cycle.
old="function savePayment(id){let amount=Number(amt.value||0);if(amount<=0)return;d.payments.push({id:Date.now().toString(),customer:id,amount,date:today(),month:month(),status:'paid',source:'manual',ref:ref.value||''});let c=d.customers.find(x=>String(x.id)===String(id));if(c){let remain=Math.max(0,due(c)-amount);if(Number(c.prevDue||0)>0){let prev=Math.max(0,Number(c.prevDue||0)-amount);c.prevDue=prev}}save();closeSheet();toast('Bill Paid');render()}"
new="function savePayment(id){let amount=Number(amt.value||0);if(amount<=0)return;let c=d.customers.find(x=>String(x.id)===String(id));if(!c)return;let beforeDue=due(c);d.payments.push({id:Date.now().toString(),customer:id,amount,date:today(),month:month(),status:'paid',source:'manual',ref:ref.value||''});let remaining=Math.max(0,beforeDue-amount);if(Number(c.prevDue||0)>0){c.prevDue=Math.max(0,Number(c.prevDue||0)-amount)}if(remaining<=0&&c.status==='expired'){c.status='active';let x=new Date();c.expiry=x.getFullYear()+'-'+pad(x.getMonth()+1)+'-'+new Date(x.getFullYear(),x.getMonth()+1,0).getDate().toString().padStart(2,'0')}save();closeSheet();toast('Bill Paid');render()}"
if old in s:
    s=s.replace(old,new)

p.write_text(s,encoding='utf-8')
print('UI/persistence patch applied')
