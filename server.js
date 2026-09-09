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
let db=null;
async function initDb(){
 if(!process.env.MONGODB_URI)throw new Error('MONGODB_URI is required for live deployment');
 if(!JWT_SECRET)throw new Error('JWT_SECRET is required for live deployment');
 if(!ADMIN_USER||!ADMIN_HASH)throw new Error('ADMIN_USER and ADMIN_PASSWORD (or ADMIN_PASSWORD_HASH) are required');
 const client=new MongoClient(process.env.MONGODB_URI); await client.connect(); db=client.db(process.env.MONGODB_DB||'star_communication');
}
function auth(req,res,next){try{const h=req.headers.authorization||'';if(!h.startsWith('Bearer '))throw 0;req.user=jwt.verify(h.slice(7),JWT_SECRET);next()}catch(e){res.status(401).json({error:'Unauthorized'})}}
function send(res,payload){res.json(payload)}
app.get('/api/health',(req,res)=>send(res,{ok:true,app:'STAR COMMUNICATION',time:new Date().toISOString(),database:!!db}));
app.post('/api/auth/login',(req,res)=>{const {username,password}=req.body||{};if(username!==ADMIN_USER||!bcrypt.compareSync(String(password||''),ADMIN_HASH))return res.status(401).json({error:'Invalid username or password'});send(res,{token:jwt.sign({username},JWT_SECRET,{expiresIn:'30d'})})});

// Minimal production API storage. If MongoDB is not configured, data lives in memory for testing only.
const mem={customers:[],payments:[],history:[],bkash:[],ledger:[]};
function col(name){return db?db.collection(name):null}
async function list(name){const c=col(name);return c?c.find({}).sort({createdAt:-1}).toArray():mem[name]}
async function insert(name,obj){const c=col(name);if(c){const r=await c.insertOne(obj);return {...obj,id:String(r.insertedId)}} mem[name].push(obj);return obj}
async function update(name,id,patch){const c=col(name);if(c){const {ObjectId}=require('mongodb');let q;try{q={_id:new ObjectId(id)}}catch{q={id}};await c.updateOne(q,{$set:patch});return}const x=mem[name].find(v=>String(v.id)===String(id));if(x)Object.assign(x,patch)}
async function remove(name,id){const c=col(name);if(c){const {ObjectId}=require('mongodb');let q;try{q={_id:new ObjectId(id)}}catch{q={id}};await c.deleteOne(q);return}mem[name].splice(mem[name].findIndex(v=>String(v.id)===String(id)),1)}
app.get('/api/customers',auth,async(req,res)=>send(res,await list('customers')));
app.post('/api/customers',auth,async(req,res)=>{const b=req.body||{};const x={id:Date.now(),name:b.name,mobile:b.mobile||'',packageName:b.packageName||'',monthlyFee:Number(b.monthlyFee||0),pppoeUsername:b.pppoeUsername||'',pppoePassword:b.pppoePassword||'',onuId:b.onuId||'',expiryDate:b.expiryDate||null,status:b.status||'ACTIVE',previousDue:Number(b.previousDue||0),createdAt:new Date().toISOString()};send(res,await insert('customers',x))});
app.delete('/api/customers/:id',auth,async(req,res)=>{await remove('customers',req.params.id);send(res,{ok:true})});
app.post('/api/customers/:id/payment',auth,async(req,res)=>{const x={id:Date.now(),customerId:req.params.id,amount:Number(req.body.amount||0),method:req.body.method||'CASH',note:req.body.note||'',month:new Date().toISOString().slice(0,7),createdAt:new Date().toISOString()};send(res,await insert('payments',x))});
app.get('/api/billing/payments',auth,async(req,res)=>send(res,await list('payments')));
app.get('/api/billing/history',auth,async(req,res)=>send(res,await list('history')));
app.post('/api/billing/ledger',auth,async(req,res)=>{const x={id:Date.now(),...req.body,amount:Number(req.body.amount||0),createdAt:new Date().toISOString()};send(res,await insert('ledger',x))});
app.get('/api/bkash/transactions',auth,async(req,res)=>send(res,await list('bkash')));
app.post('/api/bkash/transactions',auth,async(req,res)=>send(res,await insert('bkash',{id:Date.now(),...req.body,status:'PENDING',createdAt:new Date().toISOString()})));
app.post('/api/bkash/transactions/:id/manual-paid',auth,async(req,res)=>{await update('bkash',req.params.id,{status:'MANUAL_MATCHED',matchedCustomerId:req.body.customerId});send(res,{ok:true})});
app.post('/api/bkash/transactions/:id/cancel',auth,async(req,res)=>{await update('bkash',req.params.id,{status:'CANCELLED'});send(res,{ok:true})});

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
app.listen(PORT,async()=>{try{await initDb();console.log('STAR COMMUNICATION server on '+PORT)}catch(e){console.error(e);process.exit(1)}});
