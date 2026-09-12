from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

js = r'''<script>
(function(){
window.card=function(c){
  var dv=due(c), num=esc(c.phone||'');
  return `<div class="customer"><div class="cmain"><div class="avatar">${esc((c.name||'?')[0].toUpperCase())}</div><div class="grow"><div class="name">${esc(c.name||'')}</div><div class="muted">${esc(c.clientCode||'')} • ${num} • ${esc(c.pkg||'')}</div></div><span class="badge ${c.status}">${String(c.status||'').toUpperCase()}</span></div><div class="actions">${billBadge(c)}</div><div class="detail"><span>Monthly Bill</span><b>${money(c.fee)}</b></div><div class="detail"><span>Total Due</span><b>${money(dv)}</b></div><div class="actions"><button class="small view" onclick="go('details',{id:'${c.id}'})">👁 View</button><button class="small btn light" onclick="editCustomer('${c.id}')">✏️ Edit</button><button class="small call" onclick="callCustomer('${num}')">📞 Call</button><button class="small wa" onclick="waCustomer('${num}')">WhatsApp</button>${dv>0?`<button class="small pay" onclick="payCustomer('${c.id}')">Pay</button>`:''}</div></div>`;
};
window.editCustomer=function(id){
  var c=d.customers.find(function(x){return String(x.id)===String(id);});
  if(!c){toast('Customer not found');return;}
  openSheet(`<h3>✏️ Edit Customer</h3><input id="encc" class="input" value="${esc(c.clientCode||'')}" placeholder="Client Code"><input id="enn" class="input" value="${esc(c.name||'')}" placeholder="Customer name"><input id="enp" class="input" value="${esc(c.phone||'')}" placeholder="Mobile / WhatsApp"><input id="ena" class="input" value="${esc(c.address||'')}" placeholder="Address"><input id="enpkg" class="input" value="${esc(c.pkg||'')}" placeholder="Package / Mbps"><input id="enfee" class="input" type="number" value="${Number(c.fee||0)}" placeholder="Monthly fee"><input id="enpp" class="input" value="${esc(c.pppoeUser||c.pppoe||'')}" placeholder="PPPoE username"><input id="enpw" class="input" value="${esc(c.pppoePass||c.pppoePassword||'')}" placeholder="PPPoE password"><input id="enonu" class="input" value="${esc(c.onu||'')}" placeholder="ONU ID"><label class="muted">Connection Date</label><input id="encd" class="input" type="date" value="${esc(c.connectionDate||'')}"><label class="muted">Expiry Date</label><input id="enex" class="input" type="date" value="${esc(c.expiry||'')}"><input id="enprev" class="input" type="number" value="${Number(c.prevDue||0)}" placeholder="Previous due"><select id="enst" class="select"><option value="active" ${c.status==='active'?'selected':''}>Active</option><option value="inactive" ${c.status==='inactive'?'selected':''}>Inactive</option><option value="expired" ${c.status==='expired'?'selected':''}>Expired</option></select><button class="btn green full" onclick="saveCustomerEdit('${c.id}')">Save Changes</button><button class="btn light full" onclick="closeSheet()">Cancel</button>`);
};
window.saveCustomerEdit=function(id){
  var c=d.customers.find(function(x){return String(x.id)===String(id);});
  if(!c)return;
  var val=function(id){var e=document.getElementById(id);return e?e.value:'';};
  var code=val('encc').trim().toUpperCase(), name=val('enn').trim(), phone=val('enp').trim();
  if(!name||!phone){toast('Name and mobile required');return;}
  if(!code)code=c.clientCode||('SC'+String(d.customers.indexOf(c)+1).padStart(3,'0'));
  var dup=d.customers.some(function(x){return String(x.id)!==String(c.id)&&String(x.clientCode||'').toUpperCase()===code;});
  if(dup){toast('Client Code already exists');return;}
  c.clientCode=code;c.name=name;c.phone=phone;c.address=val('ena').trim();c.pkg=val('enpkg').trim();c.fee=Number(val('enfee')||0);c.pppoeUser=val('enpp').trim();c.pppoePass=val('enpw');c.onu=val('enonu').trim();c.connectionDate=val('encd')||c.connectionDate||today();c.expiry=val('enex');c.prevDue=Number(val('enprev')||0);c.status=val('enst')||'active';if(c.expiry&&c.expiry<today())c.status='expired';save();closeSheet();toast('Customer updated');render();
};
window.details=function(){
  var c=d.customers.find(function(x){return String(x.id)===String(opts.id);});
  if(!c){go('customers');return;}
  var hist=(d.payments||[]).filter(function(x){return String(x.customer)===String(c.id);}).sort(function(a,b){return String(b.date).localeCompare(String(a.date));});
  return `<h1 class="title">Customer Details</h1><div class="actions"><button class="small view" onclick="go('customers')">← Back</button><button class="small btn light" onclick="editCustomer('${c.id}')">✏️ Edit Customer</button></div><div class="customer"><div class="cmain"><div class="avatar">${esc((c.name||'?')[0].toUpperCase())}</div><div class="grow"><div class="name">${esc(c.name||'')}</div><div class="muted">Client Code: ${esc(c.clientCode||'—')} • ${esc(c.phone||'')}</div></div><span class="badge ${c.status}">${String(c.status||'').toUpperCase()}</span></div><div class="detail"><span>Client Code</span><b>${esc(c.clientCode||'—')}</b></div><div class="detail"><span>Mobile / WhatsApp</span><b>${esc(c.phone||'—')}</b></div><div class="detail"><span>Address</span><b>${esc(c.address||'—')}</b></div><div class="detail"><span>Package / Mbps</span><b>${esc(c.pkg||'—')}</b></div><div class="detail"><span>Monthly Bill</span><b>${money(c.fee)}</b></div><div class="detail"><span>PPPoE Username</span><b>${esc(c.pppoeUser||c.pppoe||'—')}</b></div><div class="detail"><span>PPPoE Password</span><b>${esc(c.pppoePass||c.pppoePassword||'—')}</b></div><div class="detail"><span>ONU ID</span><b>${esc(c.onu||'—')}</b></div><div class="detail"><span>Connection Date</span><b>${esc(c.connectionDate||'—')}</b></div><div class="detail"><span>Expiry Date</span><b>${esc(c.expiry||'—')}</b></div><div class="detail"><span>Previous Due</span><b>${money(c.prevDue)}</b></div><div class="detail"><span>Running Bill</span><b>${money(billDue(c))}</b></div><div class="detail"><span>Total Due</span><b>${money(due(c))}</b></div><div class="actions"><button class="small call" onclick="callCustomer('${esc(c.phone||'')}')">📞 Call</button><button class="small wa" onclick="waCustomer('${esc(c.phone||'')}')">WhatsApp</button>${due(c)>0?`<button class="small pay" onclick="payCustomer('${c.id}')">Customer Bill Payment</button>`:''}</div></div><div class="section"><h3>Payment History</h3>${hist.length?hist.map(function(x){return `<div class="detail"><span>${esc(x.date||'')} • ${esc(x.month||'')} • ${esc(x.source||'manual')}</span><b>${money(x.amount)}</b></div>`;}).join(''):'<div class="muted">No payments yet.</div>'}</div>`;
};
})();
</script>'''

if 'window.saveCustomerEdit=function(id)' not in s:
    s=s.replace('</body>',js+'</body>',1)
    print('Customer View/Edit patch applied')
else:
    print('Customer View/Edit patch already present')
p.write_text(s,encoding='utf-8')
