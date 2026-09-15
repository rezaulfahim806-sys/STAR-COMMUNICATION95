from pathlib import Path
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
D=chr(36)
cid=D+"{c.id}"
escp=D+"{esc(c.phone)}"
old1='<button class="small view" onclick="go(\'details\',{id:\''+cid+'\'})">Details</button>'
if "function smsCustomer(id)" not in s:
    if old1 not in s: raise SystemExit("Customer Details button not found")
    s=s.replace(old1, old1+'<button class="small view" onclick="smsCustomer(\''+cid+'\')">📩 SMS</button>',1)
old2='<button class="small wa" onclick="waCustomer(\''+escp+'\')">WhatsApp</button>'
if "function smsCustomer(id)" not in s:
    if old2 not in s: raise SystemExit("Details WhatsApp button not found")
    s=s.replace(old2, old2+'<button class="small view" onclick="smsCustomer(\''+cid+'\')">📩 SMS</button>',1)
if "function smsCustomer(id)" not in s:
    anchor="function callCustomer(n){"
    if anchor not in s: raise SystemExit("callCustomer anchor not found")
    fn=r'''function smsCustomer(id){let c=d.customers.find(x=>String(x.id)===String(id));if(!c){toast('Customer not found');return}openSheet('<h3>📩 Send SMS</h3><div class=muted>To: '+esc(c.phone||'')+' • '+esc(c.name||'Customer')+'</div><textarea id="smsmsg" class="input" rows="6" placeholder="Write message"></textarea><button class="btn dark full" onclick="sendCustomerSms(\''+c.id+'\')">📨 Send SMS</button>');}function sendCustomerSms(id){let c=d.customers.find(x=>String(x.id)===String(id));if(!c){toast('Customer not found');return}let el=document.getElementById('smsmsg'),m=el?el.value.trim():'';if(!m){toast('Write a message first');return}if(window.AndroidBridge&&AndroidBridge.sendSms){AndroidBridge.sendSms(String(c.phone||''),m);closeSheet()}else{location.href='sms:'+String(c.phone||'')+'?body='+encodeURIComponent(m);}}'''
    s=s.replace(anchor,fn+anchor,1)
p.write_text(s,encoding="utf-8")
print("Per-customer SMS compose/send option added")