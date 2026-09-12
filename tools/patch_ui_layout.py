from pathlib import Path
import re

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

# Persistent primary + backup storage.
s=s.replace("let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));",
            "let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d){try{d=JSON.parse(localStorage.getItem(KEY+'_backup')||'null')}catch(e){d=null}}if(!d)d=JSON.parse(JSON.stringify(DEF));")
s=s.replace("function save(){localStorage.setItem(KEY,JSON.stringify(d))}",
            "function save(){let s=JSON.stringify(d);localStorage.setItem(KEY,s);try{localStorage.setItem(KEY+'_backup',s)}catch(e){}}")

# Compact bottom sheet.
s=s.replace('.modal.show{display:flex}.sheet{width:min(520px,100%);max-height:92vh;overflow:auto;background:#fff;border-radius:20px 20px 0 0;padding:15px}',
            '.modal.show{display:flex}.sheet{width:min(500px,100%);max-height:78vh;overflow:auto;background:#fff;border-radius:18px 18px 0 0;padding:12px}.sheet h3{font-size:18px;margin:2px 0 8px}.sheet .input,.sheet .select{padding:8px;margin:3px 0;font-size:13px}.sheet .btn{padding:9px 11px}')

# Only one Add Customer form; status is automatic.
new_add="""function addCustomer(){openSheet(`<h3>Add Customer</h3><div class="muted" style="margin-bottom:6px">New customers are automatically Active.</div><input id="n" class="input" placeholder="Customer name"><input id="p" class="input" placeholder="Mobile / WhatsApp"><input id="a" class="input" placeholder="Address"><label class="muted">Package</label><select id="pkg" class="select"><option value="20 Mb">20 Mb</option><option value="30 Mb" selected>30 Mb</option><option value="40 Mb">40 Mb</option><option value="50 Mb">50 Mb</option></select><input id="fee" class="input" type="number" placeholder="Monthly fee"><input id="pp" class="input" placeholder="PPPoE username"><input id="pw" class="input" placeholder="PPPoE password"><input id="onu" class="input" placeholder="ONU ID"><label class="muted">Connection Date</label><input id="cd" class="input" type="date" value="${today()}"><label class="muted">Expiry Date</label><input id="ex" class="input" type="date"><input id="prev" class="input" type="number" value="0" placeholder="Previous due"><div class="detail"><span>Initial Status</span><b class="success">ACTIVE (Automatic)</b></div><button class="btn green full" onclick="saveCustomer()">Save Customer</button>`)}"""
s,n=re.subn(r'function addCustomer\(\)\{openSheet\(`.*?`\)\}\s*function saveCustomer',new_add+'function saveCustomer',s,count=1,flags=re.S)
if n!=1: raise SystemExit('Could not locate addCustomer function')

# Remove the Customers-page Add Customer button; dashboard is the single entry point.
s=re.sub(r'<button class="btn green full" onclick="addCustomer\(\)">＋ Add Customer</button>','',s)

# Add a single dashboard card where the old Total Left Client card belongs, if absent.
if '＋ Add New Customer' not in s:
    marker='<div class="stat blue" onclick="go(\'customers\',{filter:\'all\'})"><div class="label">Total Customer</div><div class="num">${d.customers.length}</div></div>'
    addcard='<div class="stat blue" onclick="addCustomer()"><div class="label">＋ Add New Customer</div><div class="num">＋</div></div>'
    s=s.replace(marker,marker+addcard,1)

# Use explicit DOM lookups; Android WebView does not reliably expose form ids as globals.
old=r"function saveCustomer\(\)\{.*?\}function payCustomer"
new="""function saveCustomer(){const nEl=document.getElementById('n'),pEl=document.getElementById('p'),aEl=document.getElementById('a'),pkgEl=document.getElementById('pkg'),feeEl=document.getElementById('fee'),ppEl=document.getElementById('pp'),pwEl=document.getElementById('pw'),onuEl=document.getElementById('onu'),cdEl=document.getElementById('cd'),exEl=document.getElementById('ex'),prevEl=document.getElementById('prev');const c={id:Date.now().toString()+Math.random().toString(36).slice(2),name:(nEl?.value||'').trim(),phone:(pEl?.value||'').trim(),address:(aEl?.value||'').trim(),pkg:pkgEl?.value||'30 Mb',fee:Number(feeEl?.value||0),pppoe:(ppEl?.value||'').trim(),pppoePassword:pwEl?.value||'',onu:(onuEl?.value||'').trim(),connectionDate:cdEl?.value||today(),expiry:exEl?.value||'',prevDue:Number(prevEl?.value||0),status:'active',createdAt:today()};if(!c.name||!c.phone){toast('Name and mobile required');return}d.customers.push(c);save();closeSheet();toast('Customer saved');go('customers',{filter:'all'},false)}function payCustomer"""
s,n=re.subn(old,new,s,count=1,flags=re.S)
if n!=1: raise SystemExit('Could not replace saveCustomer')

# Full payment on an expired customer reactivates it and sets expiry to this month-end.
oldpay=r"function savePayment\(id\)\{.*?\}function details"
newpay="""function savePayment(id){const amtEl=document.getElementById('amt'),refEl=document.getElementById('ref');let amount=Number(amtEl?.value||0);if(amount<=0)return;let c=d.customers.find(x=>String(x.id)===String(id));if(!c)return;let beforeDue=due(c);d.payments.push({id:Date.now().toString()+Math.random().toString(36).slice(2),customer:id,amount,date:today(),month:month(),status:'paid',source:'manual',ref:refEl?.value||''});let remaining=Math.max(0,beforeDue-amount);if(Number(c.prevDue||0)>0)c.prevDue=Math.max(0,Number(c.prevDue||0)-amount);if(remaining<=0&&c.status==='expired'){c.status='active';let x=new Date();let last=new Date(x.getFullYear(),x.getMonth()+1,0);c.expiry=last.getFullYear()+'-'+pad(last.getMonth()+1)+'-'+pad(last.getDate())}save();closeSheet();toast('Bill Paid');render()}function details"""
s,n=re.subn(oldpay,newpay,s,count=1,flags=re.S)
if n!=1: raise SystemExit('Could not replace savePayment')

p.write_text(s,encoding='utf-8')
print('Customer save/location patch applied')
