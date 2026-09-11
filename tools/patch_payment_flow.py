from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

repls = [
(
    '<input id="n" class="input" placeholder="Customer name"><input id="p"',
    '<input id="n" class="input" placeholder="Customer name"><input id="cc" class="input" placeholder="Client Code (e.g. SC001)"><input id="p"'
),
(
    "let c={id:Date.now().toString(),name:n.value.trim(),phone:p.value.trim(),address:a.value.trim(),",
    "let code=cc.value.trim().toUpperCase();if(!code)code='SC'+String(d.customers.length+1).padStart(3,'0');if(d.customers.some(x=>String(x.clientCode||'').toUpperCase()===code)){toast('Client Code already exists');return}let c={id:Date.now().toString(),clientCode:code,name:n.value.trim(),phone:p.value.trim(),address:a.value.trim(),"
),
(
    '<div class="muted">${num} • ${esc(c.pkg||\'\')}</div>',
    '<div class="muted">${esc(c.clientCode||\'\')} • ${num} • ${esc(c.pkg||\'\')}</div>'
),
(
    '<div class="detail"><span>Connection Date</span><b>${esc(c.connectionDate||\'—\')}</b></div><div class="detail"><span>Expiry Date</span>',
    '<div class="detail"><span>Client Code</span><b>${esc(c.clientCode||\'—\')}</b></div><div class="detail"><span>Connection Date</span><b>${esc(c.connectionDate||\'—\')}</b></div><div class="detail"><span>Expiry Date</span>'
),
(
    '<input id="sender" class="input" placeholder="Sender bKash number"><input id="inamt"',
    '<input id="sender" class="input" placeholder="Sender bKash number"><input id="incc" class="input" placeholder="Client Code (optional)"><input id="inamt"'
),
(
    "function saveIncoming(){let s=normalize(sender.value),c=d.customers.find(c=>normalize(c.phone).slice(-10)===s.slice(-10));d.pending.push({id:Date.now().toString(),sender:s,amount:Number(inamt.value||0),transactionId:tid.value||'',date:today(),status:'pending',customer:c?c.id:'',customerName:c?c.name:''});save();closeSheet();toast(c?'Matched customer — Pending':'Saved Pending');render()}",
    "function saveIncoming(){let s=normalize(sender.value),code=String(incc.value||'').trim().toUpperCase(),c=code?d.customers.find(x=>String(x.clientCode||'').toUpperCase()===code):null;if(!c&&s)c=d.customers.find(x=>normalize(x.phone).slice(-10)===s.slice(-10));d.pending.push({id:Date.now().toString(),sender:s,clientCode:code,amount:Number(inamt.value||0),transactionId:tid.value||'',date:today(),status:'pending',customer:c?c.id:'',customerName:c?c.name:'',matchedBy:c?(code?'clientCode':'number'):''});save();closeSheet();toast(c?'Matched customer — Pending':'Saved Pending');render() }"
),
(
    '<div class="muted">${esc(x.date)} • Matched: ${esc(x.customerName||\'Not matched\')}</div>',
    '<div class="muted">${esc(x.date)} • Client Code: ${esc(x.clientCode||\'—\')} • Matched: ${esc(x.customerName||\'Not matched\')}</div>'
),
(
    "function confirmPending(id){let p=d.pending.find(x=>String(x.id)===String(id));if(!p)return;let c=p.customer?d.customers.find(x=>String(x.id)===String(p.customer)):null;if(!c){let s=prompt('Customer mobile for manual match:');if(!s)return;c=d.customers.find(x=>normalize(x.phone).slice(-10)===normalize(s).slice(-10));if(!c){toast('Customer not found');return}p.customer=c.id;p.customerName=c.name}d.payments.push({id:Date.now().toString(),customer:c.id,amount:Number(p.amount||0),date:today(),month:month(),status:'paid',source:'merchant',ref:p.transactionId||''});p.status='paid';p.confirmedAt=today();save();toast('Manual Paid confirmed');render()}",
    "function confirmPending(id){let p=d.pending.find(x=>String(x.id)===String(id));if(!p)return;let c=p.customer?d.customers.find(x=>String(x.id)===String(p.customer)):null;if(!c&&p.clientCode)c=d.customers.find(x=>String(x.clientCode||'').toUpperCase()===String(p.clientCode).toUpperCase());if(!c){let code=prompt('Customer Client Code for manual match:');if(!code)return;c=d.customers.find(x=>String(x.clientCode||'').toUpperCase()===String(code).trim().toUpperCase());if(!c){toast('Customer not found');return}p.customer=c.id;p.customerName=c.name;p.clientCode=c.clientCode}d.payments.push({id:Date.now().toString(),customer:c.id,amount:Number(p.amount||0),date:today(),month:month(),status:'paid',source:'merchant',ref:p.transactionId||''});p.status='paid';p.confirmedAt=today();save();toast('Manual Paid confirmed');render()}"
]

for old, new in repls:
    if old not in s:
        raise SystemExit(f'Missing expected source pattern: {old[:100]}')
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Payment flow patch applied successfully.')
