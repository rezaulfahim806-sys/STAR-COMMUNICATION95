from pathlib import Path
p=Path("app/src/main/assets/index.html")
s=p.read_text()
old="d.settings.cloud={apiUrl:api,username:user,token:x.token};save(false);return x"
new="d.settings.cloud={apiUrl:api,username:user,token:x.token,role:x.role||'owner',owner:x.owner||user};save(false);return x"
if old not in s: raise SystemExit("cloud login marker missing")
s=s.replace(old,new,1)
old="let x=await r.json();\n  cloudLastUpdatedAt=x.updatedAt||'';"
new="""let x=await r.json();
  cloudLastUpdatedAt=x.updatedAt||'';
  if((x.role||cloudConfig().role)==='worker' && x.data){
    d.settings.cloud.role='worker'; d.settings.cloud.owner=x.owner||d.settings.cloud.owner||'';
    d.customers=x.data.customers||[]; d.payments=[]; d.expenses=[]; d.pending=[]; d.history=[];
    if(x.data.settings)d.settings=Object.assign({},d.settings,x.data.settings,{cloud:d.settings.cloud});
    localStorage.setItem(KEY,JSON.stringify(d)); render();
    return true;
  }"""
if old not in s: raise SystemExit("sync marker missing")
s=s.replace(old,new,1)
marker="function openSettings(){closeDrawer();openSheet("
insert="""function workerPage(){
 let ex=(d.customers||[]).filter(c=>String(c.status||'').toLowerCase()==='expired');
 return '<h1 class="title">Worker Panel</h1><div class="sub">Expired customer service + complaint box</div><div class="section"><h3>🔴 Expired Customers ('+ex.length+')</h3>'+ (ex.length?ex.map(c=>'<div class="customer"><div class="cmain"><div class="avatar">'+esc((c.name||'?')[0])+'</div><div class="grow"><div class="name">'+esc(c.name)+'</div><div class="muted">'+esc(c.phone)+' • '+esc(c.address||'')+'</div></div><span class="badge expired">EXPIRED</span></div><div class="actions"><button class="small call" onclick="callCustomer(\\''+esc(c.phone)+'\\')">📞 Call</button><button class="small wa" onclick="waCustomer(\\''+esc(c.phone)+'\\')">WhatsApp</button><button class="small view" onclick="workerComplaint(\\''+c.id+'\\')">📝 Complaint</button></div></div>').join(''):'<div class="muted">No expired customers.</div>')+'</div><div class="section"><h3>📝 Complaint Box</h3><button class="btn green full" onclick="workerComplaint(\\'\\')">＋ New Complaint</button><button class="btn light full" style="margin-top:7px" onclick="workerComplaints()">My Complaints</button></div>';
}
function workerComplaint(id){
 let c=d.customers.find(x=>String(x.id)===String(id));
 openSheet('<h3>📝 Submit Complaint</h3><select id="cmpCustomer" class="select"><option value="">Select customer</option>'+(d.customers||[]).map(x=>'<option value="'+x.id+'" '+(c&&String(c.id)===String(x.id)?'selected':'')+'>'+esc(x.name)+' • '+esc(x.phone)+'</option>').join('')+'</select><select id="cmpType" class="select"><option>Line Problem</option><option>Internet Slow</option><option>Connection Problem</option><option>Billing Issue</option><option>Other</option></select><textarea id="cmpMsg" class="input" rows="4" placeholder="Write complaint details"></textarea><button class="btn green full" onclick="submitComplaint()">Submit Complaint</button>');
}
async function submitComplaint(){
 let sel=document.getElementById('cmpCustomer'),c=d.customers.find(x=>String(x.id)===String(sel.value));
 let msg=document.getElementById('cmpMsg').value.trim();if(!msg){toast('Complaint details required');return}
 let cfg=cloudConfig();try{let r=await fetch(String(cfg.apiUrl).replace(/\\/$/,'')+'/api/complaints',{method:'POST',headers:cloudHeaders(),body:JSON.stringify({customerId:c?.id||'',customerName:c?.name||'',type:document.getElementById('cmpType').value,message:msg})});if(!r.ok)throw new Error('Complaint submit failed');closeSheet();toast('Complaint submitted');}catch(e){toast(e.message)}
}
async function workerComplaints(){
 let cfg=cloudConfig();try{let r=await fetch(String(cfg.apiUrl).replace(/\\/$/,'')+'/api/complaints',{headers:cloudHeaders()});if(!r.ok)throw new Error('Could not load complaints');let x=await r.json();openSheet('<h3>My Complaints</h3>'+((x.complaints||[]).length?(x.complaints||[]).map(q=>'<div class="customer"><div class="name">'+esc(q.type)+' • '+esc(q.customerName||'Customer')+'</div><div class="muted">'+esc(q.createdAt||'')+'</div><div style="margin-top:6px">'+esc(q.message)+'</div><div class="badge" style="display:inline-block;margin-top:7px">'+esc(q.status)+'</div></div>').join(''):'<div class="muted">No complaints yet.</div>'))}catch(e){toast(e.message)}
}
async function staffPanel(){
 let cfg=cloudConfig();try{let [a,c]=await Promise.all([fetch(String(cfg.apiUrl).replace(/\\/$/,'')+'/api/accounts',{headers:cloudHeaders()}),fetch(String(cfg.apiUrl).replace(/\\/$/,'')+'/api/complaints',{headers:cloudHeaders()})]);if(!a.ok||!c.ok)throw new Error('Could not load staff data');let aa=await a.json(),cc=await c.json();openSheet('<h3>👷 Worker Accounts</h3><input id="wu" class="input" placeholder="Worker username"><input id="wp" class="input" type="password" placeholder="Worker password (8+ chars)"><button class="btn green full" onclick="createWorker()">＋ Create Worker</button>'+((aa.accounts||[]).map(q=>'<div class="detail"><span>'+esc(q.username)+' • '+esc(q.role)+'</span><button class="small '+(q.active?'pay':'view')+'" onclick="toggleWorker(\\''+esc(q.username)+'\\')">'+(q.active?'Active':'Disabled')+'</button></div>').join(''))+'<hr><h3>📥 Complaint Box ('+((cc.complaints||[]).length)+')</h3>'+((cc.complaints||[]).map(q=>'<div class="customer"><div class="name">'+esc(q.customerName||'Customer')+' • '+esc(q.type)+'</div><div class="muted">By '+esc(q.createdBy)+' • '+esc(q.createdAt||'')+'</div><div style="margin-top:5px">'+esc(q.message)+'</div><button class="small pay" style="margin-top:7px" onclick="toggleComplaint(\\''+esc(q.id)+'\\',\\''+(String(q.status).toLowerCase()==='closed'?'OPEN':'CLOSED')+'\\')">'+(String(q.status).toLowerCase()==='closed'?'Reopen':'Mark Closed')+'</button></div>').join('')||'<div class="muted">No complaints.</div>')+'<button class="btn light full" style="margin-top:8px" onclick="closeSheet()">Back</button>')}catch(e){toast(e.message)}
}
async function createWorker(){let cfg=cloudConfig(),u=document.getElementById('wu').value.trim(),p=document.getElementById('wp').value;if(!u||p.length<8){toast('Username and 8+ character password required');return}try{let r=await fetch(String(cfg.apiUrl).replace(/\\/$/,'')+'/api/accounts',{method:'POST',headers:cloudHeaders(),body:JSON.stringify({username:u,password:p,role:'worker'})});if(!r.ok){let x=await r.json().catch(()=>({}));throw new Error(x.error||'Create failed')}toast('Worker created');staffPanel()}catch(e){toast(e.message)}}
async function toggleWorker(u){let cfg=cloudConfig();try{let r=await fetch(String(cfg.apiUrl).replace(/\\/$/,'')+'/api/accounts/'+encodeURIComponent(u)+'/toggle',{method:'POST',headers:cloudHeaders()});if(!r.ok)throw new Error('Update failed');staffPanel()}catch(e){toast(e.message)}}
async function toggleComplaint(id,status){let cfg=cloudConfig();try{let r=await fetch(String(cfg.apiUrl).replace(/\\/$/,'')+'/api/complaints/'+encodeURIComponent(id)+'/status',{method:'POST',headers:cloudHeaders(),body:JSON.stringify({status})});if(!r.ok)throw new Error('Update failed');staffPanel()}catch(e){toast(e.message)}}
"""
if marker not in s: raise SystemExit("settings marker missing")
s=s.replace(marker,insert+marker,1)
old="function render(){fix();let html=page==='dashboard'?dashboard():page==='customers'?customers():page==='details'?details():page==='billing'?billing():page==='analytics'?analytics():page==='accounts'?accounts():page==='monitor'?monitor():dashboard();document.getElementById('content').innerHTML=html;setNav()}"
new="function render(){fix();if(cloudConfig().role==='worker'){document.getElementById('content').innerHTML=workerPage();return}let html=page==='dashboard'?dashboard():page==='customers'?customers():page==='details'?details():page==='billing'?billing():page==='analytics'?analytics():page==='accounts'?accounts():page==='monitor'?monitor():dashboard();document.getElementById('content').innerHTML=html;setNav()}"
if old not in s: raise SystemExit("render marker missing")
s=s.replace(old,new,1)
old="<button class=\\"btn light full\\" style=\\"margin-top:7px\\" onclick=\\"cloudLogout()\\">Logout Cloud Account</button>"
new=old+"<button class=\\"btn dark full\\" style=\\"margin-top:7px\\" onclick=\\"staffPanel()\\">👷 Staff & Complaint Box</button>"
if old not in s: raise SystemExit("settings button marker missing")
s=s.replace(old,new,1)
p.write_text(s)
