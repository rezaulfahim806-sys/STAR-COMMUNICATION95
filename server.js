const express=require('express');
const cors=require('cors');
const jwt=require('jsonwebtoken');
const bcrypt=require('bcryptjs');
const {MongoClient}=require('mongodb');
const {Client:SSHClient}=require('ssh2');
const net=require('net');
require('dotenv').config();

const app=express();
app.use(cors());
app.use(express.json({limit:'1mb'}));
const PORT=process.env.PORT||10000;
const JWT_SECRET=process.env.JWT_SECRET||'';
const ADMIN_USER=process.env.ADMIN_USER||'';
const ADMIN_HASH=process.env.ADMIN_PASSWORD_HASH||((process.env.ADMIN_PASSWORD)?bcrypt.hashSync(process.env.ADMIN_PASSWORD,10):'');
const ACCOUNT_COLLECTION='accounts';
function ownerOf(u){return String(u&&u.owner||u&&u.username||'')}
function isOwner(u){return String(u&&u.role||'')==='owner'}
function isSystemAdmin(u){return !!u&&String(u.username||'')===String(ADMIN_USER)&&String(u.role||'')==='owner'}
function publicAccount(a){return {username:a.username,role:a.role,owner:a.owner,active:a.active!==false}}

let db=null;
async function initDb(){
 if(!process.env.MONGODB_URI)throw new Error('MONGODB_URI is required for live deployment');
 if(!JWT_SECRET)throw new Error('JWT_SECRET is required for live deployment');
 if(!ADMIN_USER||!ADMIN_HASH)throw new Error('ADMIN_USER and ADMIN_PASSWORD (or ADMIN_PASSWORD_HASH) are required');
 const client=new MongoClient(process.env.MONGODB_URI); await client.connect(); db=client.db(process.env.MONGODB_DB||'star_communication');
}
function auth(req,res,next){try{const h=req.headers.authorization||'';if(!h.startsWith('Bearer '))throw 0;req.user=jwt.verify(h.slice(7),JWT_SECRET);next()}catch(e){res.status(401).json({error:'Unauthorized'})}}
function send(res,payload){res.json(payload)}
app.get('/api/health',(req,res)=>send(res,{ok:true,app:'STAR COMMUNICATION',version:'1.5.3',deployment:'login-flow-update-2026-10-17',time:new Date().toISOString(),database:!!db}));
// Public read-only package lookup used by customer Payment Links.
app.get('/api/public/packages',async(req,res)=>{
 res.set('Cache-Control','no-store, no-cache, must-revalidate, proxy-revalidate');
 const company=String(req.query.company||'').trim().toLowerCase();
 if(!company||!/^[^\s@]+@gmail\.com$/i.test(company))return res.status(400).json({error:'Valid company Gmail is required'});
 const c=col('app_state');
 if(!c)return res.status(503).json({error:'Cloud database is not configured'});
 try{
  const state=await c.findOne({owner:company});
  if(!state||!state.data)return res.status(404).json({error:'Company package data not found'});
  const settings=state.data.settings||{};
  const packages=Array.isArray(settings.packages)&&settings.packages.length?settings.packages:[];
  return send(res,{ok:true,companyName:settings.cloud&&settings.cloud.companyName||'',packages,merchantNumber:String(settings.merchantNumber||'')});
 }catch(e){return res.status(500).json({error:'Could not load company packages'})}
});
app.put('/api/settings/packages',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Company owner access required'});
 const raw=req.body&&req.body.packages;
 if(!Array.isArray(raw)||raw.length>100)return res.status(400).json({error:'A package list of up to 100 items is required'});
 const packages=raw.map(p=>({speed:String(p&&p.speed||p&&p.name||'').trim(),price:Number(p&&p.price??p&&p.fee??0)}));
 if(packages.some(p=>!p.speed||p.speed.length>80||!Number.isFinite(p.price)||p.price<=0))return res.status(400).json({error:'Every package needs a name and a price greater than zero'});
 const c=col('app_state');if(!c)return res.status(503).json({error:'Cloud database is not configured'});
 const owner=ownerOf(req.user),now=new Date().toISOString();
 const state=await c.findOne({owner});
 if(!state){
  await c.insertOne({owner,data:{customers:[],payments:[],expenses:[],pending:[],history:[],settings:{packages}},updatedAt:now});
 }else{
  await c.updateOne({owner},{$set:{'data.settings.packages':packages,updatedAt:now}});
 }
 return send(res,{ok:true,packages,updatedAt:now,message:'Packages published to customer payment links'});
});
app.post('/api/auth/register',async(req,res)=>{
 const {email,password,companyName}=req.body||{};
 const u=String(email||'').trim().toLowerCase(), p=String(password||''), company=String(companyName||'').trim();
 if(!/^[^\s@]+@gmail\.com$/i.test(u))return res.status(400).json({error:'A valid Gmail address is required'});
 if(u===String(ADMIN_USER).trim().toLowerCase())return res.status(409).json({error:'This Gmail is reserved for the system administrator'});
 if(p.length<8)return res.status(400).json({error:'Password must be at least 8 characters'});
 if(company.length<2||company.length>100)return res.status(400).json({error:'Company name is required'});
 try{
  const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
  if(await ac.findOne({username:u}))return res.status(409).json({error:'This Gmail account is already registered'});
  const a={username:u,email:u,companyName:company,passwordHash:bcrypt.hashSync(p,12),role:'owner',owner:u,active:false,approvalStatus:'pending',createdAt:new Date().toISOString()};
  await ac.insertOne(a);
  return res.status(202).json({ok:true,pending:true,message:'Registration submitted. Wait for administrator approval before logging in.',username:u,companyName:company});
 }catch(e){res.status(500).json({error:'Registration service error'})}
});

// System-admin approval queue for newly registered ISP/company accounts.
app.get('/api/admin/registrations',auth,async(req,res)=>{
 if(!isSystemAdmin(req.user))return res.status(403).json({error:'System administrator access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const accounts=await ac.find({approvalStatus:'pending'}).sort({createdAt:1}).project({passwordHash:0}).toArray();
 send(res,{ok:true,registrations:accounts.map(a=>({username:a.username,email:a.email||a.username,companyName:a.companyName||'',createdAt:a.createdAt,status:a.approvalStatus||'pending'}))});
});
app.post('/api/admin/registrations/:username/approve',auth,async(req,res)=>{
 if(!isSystemAdmin(req.user))return res.status(403).json({error:'System administrator access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const u=String(req.params.username||'').trim().toLowerCase();
 const result=await ac.updateOne({username:u,approvalStatus:'pending'},{$set:{active:true,approvalStatus:'approved',approvedAt:new Date().toISOString(),approvedBy:req.user.username}});
 if(!result.matchedCount)return res.status(404).json({error:'Pending registration not found'});
 send(res,{ok:true,message:'Registration approved',username:u});
});
app.post('/api/admin/registrations/:username/reject',auth,async(req,res)=>{
 if(!isSystemAdmin(req.user))return res.status(403).json({error:'System administrator access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const u=String(req.params.username||'').trim().toLowerCase();
 const result=await ac.updateOne({username:u,approvalStatus:'pending'},{$set:{active:false,approvalStatus:'rejected',rejectedAt:new Date().toISOString(),rejectedBy:req.user.username}});
 if(!result.matchedCount)return res.status(404).json({error:'Pending registration not found'});
 send(res,{ok:true,message:'Registration rejected',username:u});
});

app.post('/api/auth/password',auth,async(req,res)=>{
 const current=String(req.body&&req.body.currentPassword||'');
 const next=String(req.body&&req.body.newPassword||'');
 if(next.length<8)return res.status(400).json({error:'New password must be at least 8 characters'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const account=await ac.findOne({username:req.user.username,owner:ownerOf(req.user)});
 if(!account)return res.status(400).json({error:'This account password is managed by the server administrator'});
 if(!bcrypt.compareSync(current,account.passwordHash))return res.status(401).json({error:'Current password is incorrect'});
 await ac.updateOne({_id:account._id},{$set:{passwordHash:bcrypt.hashSync(next,12),passwordUpdatedAt:new Date().toISOString()}});
 return send(res,{ok:true,message:'Password updated'});
});
app.post('/api/auth/login',async(req,res)=>{
 const {username,password}=req.body||{};
 const u=String(username||'').trim(), p=String(password||'');
 if(!u||!p)return res.status(400).json({error:'Username and password are required'});
 try{
  let account=null;
  const ac=col(ACCOUNT_COLLECTION);
  if(ac)account=await ac.findOne({username:u});
  if(account){
   if(!bcrypt.compareSync(p,account.passwordHash))return res.status(401).json({error:'Invalid username or password'});
   if(account.approvalStatus==='pending'||account.active===false)return res.status(403).json({error:'Your registration is pending administrator approval'});
   if(account.approvalStatus==='rejected')return res.status(403).json({error:'Your registration was not approved. Contact the administrator'});
   const claims={username:account.username,role:account.role||'worker',owner:account.owner||account.username};
   const token=jwt.sign(claims,JWT_SECRET,{expiresIn:'30d'});
   return send(res,{token,expiresIn:30*24*60*60,role:claims.role,owner:claims.owner,username:claims.username});
  }
  if(u!==ADMIN_USER||!ADMIN_HASH||!bcrypt.compareSync(p,ADMIN_HASH))return res.status(401).json({error:'Invalid username or password'});
  const token=jwt.sign({username:u,role:'owner',owner:u},JWT_SECRET,{expiresIn:'30d'});
  send(res,{token,expiresIn:30*24*60*60,role:'owner',owner:u,username:u});
 }catch(e){res.status(500).json({error:'Login service error'})}
});

// Minimal production API storage. If MongoDB is not configured, data lives in memory for testing only.
const mem={customers:[],payments:[],history:[],bkash:[],ledger:[]};
function col(name){return db?db.collection(name):null}
async function list(name,owner){const c=col(name);return c?c.find({owner:String(owner)}).sort({createdAt:-1}).toArray():mem[name].filter(v=>String(v.owner)===String(owner))}
async function insert(name,obj,owner){const x={...obj,owner:String(owner)};const c=col(name);if(c){const r=await c.insertOne(x);return {...x,id:String(r.insertedId)}} mem[name].push(x);return x}
async function update(name,id,patch,owner){const c=col(name);if(c){const {ObjectId}=require('mongodb');let q;try{q={_id:new ObjectId(id),owner:String(owner)}}catch{q={id,owner:String(owner)}};await c.updateOne(q,{$set:patch});return}const x=mem[name].find(v=>String(v.id)===String(id)&&String(v.owner)===String(owner));if(x)Object.assign(x,patch)}
async function remove(name,id,owner){const c=col(name);if(c){const {ObjectId}=require('mongodb');let q;try{q={_id:new ObjectId(id),owner:String(owner)}}catch{q={id,owner:String(owner)}};await c.deleteOne(q);return}const i=mem[name].findIndex(v=>String(v.id)===String(id)&&String(v.owner)===String(owner));if(i>=0)mem[name].splice(i,1)}
// Staff accounts: owner can create worker logins. Workers share the owner's customer cloud but are restricted to expired clients and complaints.
app.post('/api/accounts',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Owner access required'});
 const {username,password}=req.body||{}, role=String(req.body&&req.body.role||'worker');
 const u=String(username||'').trim(), p=String(password||'');
 if(!/^[A-Za-z0-9_.-]{3,32}$/.test(u)||p.length<8)return res.status(400).json({error:'Username 3-32 chars and password at least 8 chars required'});
 if(role!=='worker')return res.status(400).json({error:'Only worker sub-accounts can be created'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 if(await ac.findOne({username:u}))return res.status(409).json({error:'Username already exists'});
 const a={username:u,passwordHash:bcrypt.hashSync(p,12),role:'worker',owner:ownerOf(req.user),active:true,createdAt:new Date().toISOString()};
 await ac.insertOne(a);send(res,{ok:true,account:publicAccount(a)});
});
app.get('/api/accounts',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Owner access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return send(res,{ok:true,accounts:[]});
 send(res,{ok:true,accounts:(await ac.find({owner:ownerOf(req.user)}).sort({createdAt:-1}).toArray()).map(publicAccount)});
});
app.post('/api/accounts/:username/toggle',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Owner access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const a=await ac.findOne({username:req.params.username,owner:ownerOf(req.user)});
 if(!a)return res.status(404).json({error:'Account not found'});
 await ac.updateOne({_id:a._id},{$set:{active:a.active===false}});
 send(res,{ok:true,active:a.active===false});
});
app.post('/api/complaints',auth,async(req,res)=>{
 const c=col('complaints');if(!c)return res.status(503).json({error:'Cloud database is not configured'});
 const b=req.body||{};const x={id:Date.now().toString(),owner:ownerOf(req.user),createdBy:req.user.username,customerId:String(b.customerId||''),customerName:String(b.customerName||''),type:String(b.type||'General'),message:String(b.message||'').trim(),status:'OPEN',createdAt:new Date().toISOString()};
 if(!x.message)return res.status(400).json({error:'Complaint message is required'});
 await c.insertOne(x);send(res,{ok:true,complaint:x});
});
app.get('/api/complaints',auth,async(req,res)=>{
 const c=col('complaints');if(!c)return send(res,{ok:true,complaints:[]});
 const q={owner:ownerOf(req.user)};if(!isOwner(req.user))q.createdBy=req.user.username;
 send(res,{ok:true,complaints:await c.find(q).sort({createdAt:-1}).limit(200).toArray()});
});
app.post('/api/complaints/:id/status',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Owner access required'});
 const c=col('complaints');if(!c)return res.status(503).json({error:'Cloud database is not configured'});
 await c.updateOne({id:String(req.params.id),owner:ownerOf(req.user)},{$set:{status:String(req.body&&req.body.status||'OPEN'),updatedAt:new Date().toISOString(),handledBy:req.user.username}});
 send(res,{ok:true});
});
// Cloud sync: one account can use the same data on multiple devices.
app.get('/api/sync',auth,async(req,res)=>{
 const c=col('app_state');
 if(!c)return send(res,{ok:true,data:null});
 const state=await c.findOne({owner:ownerOf(req.user)});
 if(!state)return send(res,{ok:true,data:null,updatedAt:null,role:req.user.role||'owner',owner:ownerOf(req.user)});
 if(isOwner(req.user))return send(res,{ok:true,data:state.data,updatedAt:state.updatedAt,role:'owner',owner:ownerOf(req.user)});
 const safe={customers:(state.data.customers||[]).filter(x=>String(x.status||'').toLowerCase()==='expired'),payments:[],expenses:[],pending:[],history:[],settings:{cloud:{}}};
 send(res,{ok:true,data:safe,updatedAt:state.updatedAt,role:'worker',owner:ownerOf(req.user)});
});
app.post('/api/sync',auth,async(req,res)=>{
 const data=req.body&&req.body.data;
 if(!data||!Array.isArray(data.customers)||!Array.isArray(data.payments)||!Array.isArray(data.expenses)||!Array.isArray(data.pending)||!Array.isArray(data.history))
   return res.status(400).json({error:'Invalid sync data'});
 const clean={
   customers:data.customers,
   payments:data.payments,
   expenses:data.expenses,
   pending:data.pending,
   history:data.history,
   settings:data.settings||{}
 };
 const c=col('app_state');
 if(!c)return res.status(503).json({error:'Cloud database is not configured'});
 const now=new Date().toISOString();
 const owner=ownerOf(req.user);
 if(!isOwner(req.user))return res.status(403).json({error:'Workers cannot upload company data'});
 // Reject stale device writes; clients should sync/merge before retrying.
 const incomingUpdatedAt=String(req.body.updatedAt||'');
 const existing=await c.findOne({owner});
 if(existing&&incomingUpdatedAt&&existing.updatedAt&&incomingUpdatedAt<existing.updatedAt){
   return res.status(409).json({error:'Cloud data changed on another device; sync before upload',updatedAt:existing.updatedAt,data:existing.data});
 }
 if(existing&&existing.data){
   const backups=db.collection('app_state_backups');
   await backups.insertOne({owner,sourceUpdatedAt:existing.updatedAt||null,savedAt:now,data:existing.data});
   const oldBackups=await backups.find({owner}).sort({savedAt:-1}).skip(20).toArray();
   if(oldBackups.length) await backups.deleteMany({_id:{$in:oldBackups.map(x=>x._id)}});
 }
 await c.updateOne({owner},{$set:{owner,data:clean,updatedAt:now}},{upsert:true});
 send(res,{ok:true,updatedAt:now,backupCreated:!!existing});
});
app.get('/api/sync/backups',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Owner access required'});
 const c=db&&db.collection('app_state_backups');
 if(!c)return send(res,{ok:true,backups:[]});
 const rows=await c.find({owner:req.user.username},{projection:{data:0}}).sort({savedAt:-1}).limit(20).toArray();
 send(res,{ok:true,backups:rows});
});
app.get('/api/customers',auth,async(req,res)=>send(res,await list('customers',ownerOf(req.user))));
app.post('/api/customers',auth,async(req,res)=>{const b=req.body||{};const x={id:Date.now(),name:b.name,mobile:b.mobile||'',packageName:b.packageName||'',monthlyFee:Number(b.monthlyFee||0),pppoeUsername:b.pppoeUsername||'',pppoePassword:b.pppoePassword||'',onuId:b.onuId||'',expiryDate:b.expiryDate||null,status:b.status||'ACTIVE',previousDue:Number(b.previousDue||0),createdAt:new Date().toISOString()};send(res,await insert('customers',x,ownerOf(req.user)))});
app.delete('/api/customers/:id',auth,async(req,res)=>{await remove('customers',req.params.id,ownerOf(req.user));send(res,{ok:true})});
app.post('/api/customers/:id/payment',auth,async(req,res)=>{const x={id:Date.now(),customerId:req.params.id,amount:Number(req.body.amount||0),method:req.body.method||'CASH',note:req.body.note||'',month:new Date().toISOString().slice(0,7),createdAt:new Date().toISOString()};send(res,await insert('payments',x,ownerOf(req.user)))});
app.get('/api/billing/payments',auth,async(req,res)=>send(res,await list('payments',ownerOf(req.user))));
app.get('/api/billing/history',auth,async(req,res)=>send(res,await list('history',ownerOf(req.user))));
app.post('/api/billing/ledger',auth,async(req,res)=>{const x={id:Date.now(),...req.body,amount:Number(req.body.amount||0),createdAt:new Date().toISOString()};send(res,await insert('ledger',x,ownerOf(req.user)))});
app.get('/api/bkash/transactions',auth,async(req,res)=>send(res,await list('bkash',ownerOf(req.user))));
app.post('/api/bkash/transactions',auth,async(req,res)=>send(res,await insert('bkash',{id:Date.now(),...req.body,status:'PENDING',createdAt:new Date().toISOString()},ownerOf(req.user))));
app.post('/api/bkash/transactions/:id/manual-paid',auth,async(req,res)=>{await update('bkash',req.params.id,{status:'MANUAL_MATCHED',matchedCustomerId:req.body.customerId},ownerOf(req.user));send(res,{ok:true})});
app.post('/api/bkash/transactions/:id/cancel',auth,async(req,res)=>{await update('bkash',req.params.id,{status:'CANCELLED'},ownerOf(req.user));send(res,{ok:true})});

function sshExec({host,port,user,password,command,timeout=12000}){return new Promise((resolve,reject)=>{const c=new SSHClient();let out='',err='';const timer=setTimeout(()=>{c.end();reject(new Error('OLT SSH timeout'))},timeout);c.on('ready',()=>c.exec(command,(e,s)=>{if(e){clearTimeout(timer);c.end();return reject(e)}s.on('data',d=>out+=d.toString());s.stderr.on('data',d=>err+=d.toString());s.on('close',()=>{clearTimeout(timer);c.end();resolve({out,err})})})).on('error',e=>{clearTimeout(timer);reject(e)}).connect({host,port:Number(port||22),username:user,password,readyTimeout:timeout,hostVerifier:()=>true})})}
function vsolSshExec({host,port,user,password,command,timeout=18000}){return new Promise((resolve,reject)=>{const c=new SSHClient();let out='',err='',stage='start',done=false;const timer=setTimeout(()=>finish(new Error('VSOL SSH timeout')),timeout);const finish=(e)=>{if(done)return;done=true;clearTimeout(timer);try{c.end()}catch{};e?reject(e):resolve({out,err})};c.on('ready',()=>c.shell({term:'vt100'},(e,stream)=>{if(e)return finish(e);const write=x=>{try{stream.write(x+'\n')}catch(err){finish(err)}};stream.on('data',d=>{out+=d.toString();const tail=out.slice(-1400);if(/(?:login|username)\s*[:>]/i.test(tail)&&stage==='start'){write(user);stage='login';return}if(/password\s*[:>]/i.test(tail)&&stage!=='password'&&stage!=='config'&&stage!=='command'){write(password);stage='password';return}if(stage==='start'&&/>\s*$/.test(tail)){write('enable');stage='enable';return}if(stage==='start'&&/#\s*$/.test(tail)){write('configure terminal');stage='config';return}if((stage==='enable'||stage==='password')&&/#\s*$/.test(tail)){write('configure terminal');stage='config';return}if(stage==='config'&&/\(config[^)]*\)#\s*$/.test(tail)){write(command);stage='command';return}if(stage==='command'&&/\n[^\r\n]{0,100}[#>]\s*$/.test(tail)){setTimeout(()=>finish(),900)}});stream.stderr?.on('data',d=>err+=d.toString());stream.on('close',()=>finish())})).on('error',e=>finish(e)).connect({host,port:Number(port||22),username:user,password,readyTimeout:timeout,hostVerifier:()=>true})})}

function telnetExec({host,port,user,password,command,timeout=12000}){return new Promise((resolve,reject)=>{const s=net.createConnection({host,port:Number(port||23)});let buf='',lastAction='';const timer=setTimeout(()=>{s.destroy();reject(new Error('OLT Telnet timeout'))},timeout);const sendOnce=(x)=>{if(lastAction===x)return;lastAction=x;s.write(x+'\n')};s.on('data',d=>{buf+=d.toString();const tail=buf.slice(-500);if(/password\s*[:>]/i.test(tail))sendOnce(password);else if(/login|username\s*[:>]/i.test(tail))sendOnce(user);else if(/[#>]\s*$/.test(tail)){sendOnce(command);setTimeout(()=>s.end(),2200)}});s.on('close',()=>{clearTimeout(timer);resolve({out:buf,err:''})});s.on('error',e=>{clearTimeout(timer);reject(e)})})}
function parseVsolOnuRows(raw){
 const rows=[];
 for(const line of String(raw||'').split(/\r?\n/)){
  const m=line.match(/^(EPON\d+\/\d+:\d+)\s+(online|offline)\s+([0-9a-f:.-]+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.*?)\s+(\d+\s+\d+:\d+)\s*$/i);
  if(m) rows.push({onuId:m[1],status:m[2].toLowerCase(),mac:m[3],distanceM:Number(m[4]),rtt:Number(m[5]),lastRegister:m[6],lastDeregister:m[7],lastDeregisterReason:m[8].trim(),aliveTime:m[9].trim()});
 }
 return rows;
}
function parseOnuCounts(raw,vendor){const t=String(raw||'');let online=0,offline=0,total=0;const v=String(vendor||'').toLowerCase();if(v==='vsol'){const lines=t.split(/\r?\n/);for(const line of lines){if(!/EPON\d+\/\d+\s*:\s*\d+/i.test(line))continue;const m=line.match(/EPON\d+\/\d+\s*:\s*\d+\s+(online|offline)\b/i);if(m){total++;if(m[1].toLowerCase()==='online')online++;else offline++}}return {total:total||null,online:total?online:null,offline:total?offline:null}}const m=t.match(/(?:total|all|onu)\D{0,20}(\d+)\D{0,20}(?:online|up)\D{0,20}(\d+)\D{0,20}(?:offline|down)\D{0,20}(\d+)/i);if(m){total=+m[1];online=+m[2];offline=+m[3]}return {total:total||null,online:online||null,offline:offline||null}}
function commandFor(vendor,action){const v=String(vendor||'generic').toLowerCase();if(action==='summary'){if(v==='vsol')return 'show onu status all';if(v==='huawei')return 'display ont info summary';if(v==='zte')return 'show gpon onu state';if(v==='fiberhome')return 'show onu status';return 'show onu status'}if(action==='version'){if(v==='vsol')return 'show version';if(v==='huawei')return 'display version';if(v==='zte')return 'show version';return 'show version'}if(action==='config'){if(v==='vsol')return 'show running-config';return 'show running-config'}return action}
async function runOltCommand({host,port,user,password,protocol,vendor,command}){const isTelnet=String(protocol||'ssh').toLowerCase()==='telnet';if(isTelnet)return telnetExec({host,port:port||23,user,password,command});if(String(vendor||'').toLowerCase()==='vsol')return vsolSshExec({host,port:port||22,user,password,command});return sshExec({host,port:port||22,user,password,command})}
app.post('/api/olt/test',auth,async(req,res)=>{const {host,port,protocol,user,password,vendor}=req.body||{};if(!host||!user||!password)return res.status(400).json({error:'OLT IP, username and password are required'});try{const cmd=commandFor(vendor,'version');const r=await runOltCommand({host,port,user,password,protocol,vendor,command:cmd});send(res,{ok:true,connected:true,protocol:protocol||'ssh',vendor:vendor||'generic',output:r.out.slice(-8000)})}catch(e){res.status(502).json({error:'OLT connection failed: '+e.message})}});
app.post('/api/olt/monitor',auth,async(req,res)=>{const {host,port,protocol,user,password,vendor}=req.body||{};if(!host||!user||!password)return res.status(400).json({error:'OLT IP, username and password are required'});try{const cmd=commandFor(vendor,'summary');const r=await runOltCommand({host,port,user,password,protocol,vendor,command:cmd});const counts=parseOnuCounts(r.out,vendor);send(res,{ok:true,connected:true,vendor:vendor||'generic',raw:r.out.slice(-15000),...counts,parser:'heuristic'})}catch(e){res.status(502).json({error:'OLT monitor failed: '+e.message})}});
app.post('/api/olt/onu-list',auth,async(req,res)=>{const {host,port,protocol,user,password,vendor}=req.body||{};if(!host||!user||!password)return res.status(400).json({error:'OLT IP, username and password are required'});if(String(vendor||'').toLowerCase()!=='vsol')return res.status(400).json({error:'Live ONU list is currently implemented for VSOL EPON'});try{const r=await runOltCommand({host,port, user,password,protocol,vendor,command:'show onu status all'});const rows=parseVsolOnuRows(r.out);const counts=parseOnuCounts(r.out,'vsol');send(res,{ok:true,connected:true,vendor:'vsol',rows,...counts,raw:r.out.slice(-20000)})}catch(e){res.status(502).json({error:'VSOL ONU list failed: '+e.message})}});
app.use(express.static(require('path').join(__dirname,'app','src','main','assets')));

function readApiPath(obj,path){
 if(!path)return undefined;
 return String(path).split('.').reduce((v,k)=>v==null?undefined:v[k],obj);
}
function configuredHttpsUrl(raw){
 let u;try{u=new URL(String(raw||''))}catch(e){throw new Error('A valid HTTPS API URL is required')}
 if(u.protocol!=='https:'||!u.hostname||u.username||u.password)throw new Error('API endpoint must use HTTPS');
 const h=u.hostname.toLowerCase();
 if(h==='localhost'||h==='127.0.0.1'||h==='::1'||h.endsWith('.local'))throw new Error('Local API endpoints are not allowed');
 return u;
}
async function integrationSettings(owner){
 const c=col('app_state');if(!c)throw new Error('Cloud database is not configured');
 const state=await c.findOne({owner:String(owner)});
 if(!state||!state.data)throw new Error('Company cloud settings not found');
 return state.data.settings||{};
}
async function callConfiguredApi(cfg,{transactionId,amount,customerId,phone,message}){
 const u=configuredHttpsUrl(cfg.url);
 const method=String(cfg.method||'POST').toUpperCase()==='GET'?'GET':'POST';
 const key=String(cfg.apiKey||'').trim();
 if(!key)throw new Error('API key/token is missing in Settings');
 const payload={transactionId:transactionId||'',trxID:transactionId||'',amount:Number(amount||0),customerId:customerId||'',to:phone||'',phone:phone||'',message:message||'',senderid:cfg.senderId||'',senderId:cfg.senderId||''};
 const keyField=String(cfg.apiKeyField||'').trim();
 if(keyField)payload[keyField]=key;
 const headers={'Accept':'application/json','Authorization':'Bearer '+key,'x-api-key':key};
 let body;
 if(method==='GET'){
  Object.entries(payload).forEach(([k,v])=>{if(v!==''&&v!==undefined)u.searchParams.set(k,String(v))});
 }else{
  headers['Content-Type']='application/json';
  body=JSON.stringify(payload);
 }
 const controller=new AbortController();
 const timer=setTimeout(()=>controller.abort(),12000);
 try{
  const response=await fetch(u,{method,headers,body,signal:controller.signal,redirect:'error'});
  const raw=await response.text();let data={};try{data=raw?JSON.parse(raw):{}}catch(e){data={message:raw.slice(0,300)}}
  if(!response.ok)throw new Error('Provider API returned HTTP '+response.status);
  return {data,status:response.status};
 }finally{clearTimeout(timer)}
}
app.post('/api/integrations/sms/send',auth,async(req,res)=>{
 try{
  const phone=String(req.body&&req.body.phone||'').trim(),message=String(req.body&&req.body.message||'').trim();
  if(!phone||!message)return res.status(400).json({error:'Phone and message are required'});
  if(message.length>1200)return res.status(400).json({error:'Message is too long'});
  const settings=await integrationSettings(ownerOf(req.user)),cfg=settings.smsApi||{};
  if(!cfg.url)return res.status(400).json({error:'Configure the SMS API endpoint in Settings first'});
  const result=await callConfiguredApi({...cfg,apiKeyField:cfg.apiKeyField,senderId:cfg.senderId},{phone,message});
  const d=result.data||{};
  if(d.success===false||d.ok===false||String(d.status||'').toLowerCase()==='error')return res.status(502).json({error:'SMS provider reported failure',providerMessage:String(d.message||d.error||'').slice(0,180)});
  send(res,{ok:true,message:'SMS request accepted by provider',providerResponse:d});
 }catch(e){res.status(502).json({error:'SMS API failed: '+String(e.message||'Request failed').slice(0,180)})}
});
app.post('/api/billing/verify-payment',auth,async(req,res)=>{
 try{
  const transactionId=String(req.body&&req.body.transactionId||'').trim();
  const customerId=String(req.body&&req.body.customerId||'').trim();
  const amount=Number(req.body&&req.body.amount||0);
  if(!transactionId||!customerId||!Number.isFinite(amount)||amount<=0)return res.status(400).json({error:'Customer, transaction ID and amount are required'});
  const settings=await integrationSettings(ownerOf(req.user)),cfg=settings.paymentVerify||{};
  if(!cfg.url)return res.status(400).json({error:'Configure the payment verification API in Settings first'});
  const result=await callConfiguredApi({...cfg,apiKeyField:cfg.apiKeyField},{transactionId,amount,customerId});
  const data=result.data||{};
  const statusPath=String(cfg.statusPath||'status');
  const amountPath=String(cfg.amountPath||'amount');
  const transactionPath=String(cfg.transactionPath||'transactionId');
  const statusValue=readApiPath(data,statusPath)??data.transactionStatus??data.paymentStatus??data.status??data.result?.status??data.data?.status;
  const amountValue=readApiPath(data,amountPath)??data.trxAmount??data.transactionAmount??data.data?.amount;
  const transactionValue=readApiPath(data,transactionPath)??data.trxID??data.trxId??data.data?.trxID;
  const normalized=String(statusValue||'').trim().toLowerCase();
  if(!['paid','success','successful','completed','complete','approved','verified'].includes(normalized))return res.status(409).json({ok:false,verified:false,error:'Provider did not confirm a successful payment',providerStatus:String(statusValue||'unknown')});
  if(amountValue===undefined||amountValue===null||!Number.isFinite(Number(amountValue))||Math.abs(Number(amountValue)-amount)>0.01)return res.status(409).json({ok:false,verified:false,error:'Provider amount does not match the bill'});
  if(transactionValue&&String(transactionValue).trim().toLowerCase()!==transactionId.toLowerCase())return res.status(409).json({ok:false,verified:false,error:'Provider transaction ID does not match'});
  send(res,{ok:true,verified:true,transactionId,amount:Number(amountValue),providerStatus:String(statusValue),message:'Payment verified by configured provider API'});
 }catch(e){res.status(502).json({ok:false,verified:false,error:'Payment verification failed: '+String(e.message||'Request failed').slice(0,180)})}
});

app.listen(PORT,async()=>{try{await initDb();console.log('STAR COMMUNICATION server on '+PORT)}catch(e){console.error(e);process.exit(1)}});
