const express=require('express');
const cors=require('cors');
const jwt=require('jsonwebtoken');
const bcrypt=require('bcryptjs');
const {MongoClient}=require('mongodb');
const {Client:SSHClient}=require('ssh2');
const net=require('net');
const crypto=require('crypto');
const nodemailer=require('nodemailer');
require('dotenv').config();

const app=express();
app.use(cors());
app.use(express.json({limit:'1mb',verify:(req,res,buf)=>{req.rawBody=Buffer.from(buf)}}));
const PORT=process.env.PORT||10000;
const JWT_SECRET=process.env.JWT_SECRET||'';
const ADMIN_USER=process.env.ADMIN_USER||'';
const ADMIN_HASH=process.env.ADMIN_PASSWORD_HASH||((process.env.ADMIN_PASSWORD)?bcrypt.hashSync(process.env.ADMIN_PASSWORD,10):'');
const ACCOUNT_COLLECTION='accounts';
function ownerOf(u){return String(u&&u.owner||u&&u.username||'')}
function isOwner(u){return String(u&&u.role||'')==='owner'}
function isSystemAdmin(u){return !!u&&!!ADMIN_USER&&String(u.username||'').trim().toLowerCase()===String(ADMIN_USER).trim().toLowerCase()&&String(u.role||'')==='owner'}
async function sendApprovalEmail(to,companyName){const host=process.env.SMTP_HOST,user=process.env.SMTP_USER,pass=process.env.SMTP_PASS,from=process.env.SMTP_FROM||user;if(!host||!user||!pass||!from)return {sent:false,reason:'SMTP is not configured'};const transporter=nodemailer.createTransport({host,port:Number(process.env.SMTP_PORT||587),secure:String(process.env.SMTP_SECURE||'false')==='true',auth:{user,pass}});await transporter.sendMail({from,to,subject:'STAR COMMUNICATION account approved',text:'Hello '+companyName+',\n\nYour STAR COMMUNICATION company account has been approved. You can now log in to the STAR COMMUNICATION app using this Gmail address and the password you created.\n\nSTAR COMMUNICATION',html:'<p>Hello '+String(companyName||'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]))+',</p><p>Your STAR COMMUNICATION company account has been approved. You can now log in to the STAR COMMUNICATION app using this Gmail address and the password you created.</p><p>STAR COMMUNICATION</p>'});return {sent:true}}
function publicAccount(a){return {username:a.username,role:a.role,owner:a.owner,active:a.active!==false}}
function flagEnabled(value){return value===true||['true','1','yes','on','enabled'].includes(String(value??'').trim().toLowerCase())}
function packageChoiceEnabled(customer){return !!customer&&(flagEnabled(customer.allowPackageChoice)||flagEnabled(customer.allowPackageChange))}

let db=null;
async function initDb(){
 if(!process.env.MONGODB_URI)throw new Error('MONGODB_URI is required for live deployment');
 if(!JWT_SECRET)throw new Error('JWT_SECRET is required for live deployment');
 if(!ADMIN_USER||!ADMIN_HASH)throw new Error('ADMIN_USER and ADMIN_PASSWORD (or ADMIN_PASSWORD_HASH) are required');
 const client=new MongoClient(process.env.MONGODB_URI); await client.connect(); db=client.db(process.env.MONGODB_DB||'star_communication');
}
async function auth(req,res,next){try{const h=req.headers.authorization||'';if(!h.startsWith('Bearer '))throw 0;req.user=jwt.verify(h.slice(7),JWT_SECRET);if(isSystemAdmin(req.user))return next();const ac=col(ACCOUNT_COLLECTION);if(ac){const u=String(req.user.username||'').trim().toLowerCase();const owner=String(req.user.owner||u).trim().toLowerCase();const account=await ac.findOne({username:owner});if(account&&(account.accountStatus==='disabled'||account.active===false||account.approvalStatus==='pending'||account.approvalStatus==='rejected'))return res.status(403).json({error:String(account.disabledMessage||(account.approvalStatus==='pending'?'Your company registration is awaiting approval':'এই কোম্পানির অ্যাকাউন্ট STAR COMMUNICATION Admin বন্ধ রেখেছেন। অনুগ্রহ করে Admin-এর সঙ্গে যোগাযোগ করুন।')).slice(0,500),accountDisabled:true});}next()}catch(e){res.status(401).json({error:'Unauthorized'})}}
function send(res,payload){res.json(payload)}
const BKASH_BASE_URL=(process.env.BKASH_BASE_URL||'https://checkout.sandbox.bka.sh/v1.2.0-beta').replace(/\/$/,'');
const BKASH_APP_KEY=process.env.BKASH_APP_KEY||'';
const BKASH_APP_SECRET=process.env.BKASH_APP_SECRET||'';
const BKASH_USERNAME=process.env.BKASH_USERNAME||'';
const BKASH_PASSWORD=process.env.BKASH_PASSWORD||'';
const PUBLIC_URL=(process.env.PUBLIC_URL||'https://star-communication-api.onrender.com').replace(/\/$/,'');
const PAYMENT_PAGE_URL=process.env.PAYMENT_PAGE_URL||'https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html';
let bkashTokenCache={token:'',expiresAt:0};
async function getBkashToken(){
 if(!BKASH_APP_KEY||!BKASH_APP_SECRET||!BKASH_USERNAME||!BKASH_PASSWORD)throw new Error('bKash API credentials are not configured in Render Environment Variables');
 if(bkashTokenCache.token&&Date.now()<bkashTokenCache.expiresAt)return bkashTokenCache.token;
 const r=await fetch(BKASH_BASE_URL+'/checkout/token/grant',{method:'POST',headers:{accept:'application/json','content-type':'application/json',username:BKASH_USERNAME,password:BKASH_PASSWORD},body:JSON.stringify({app_key:BKASH_APP_KEY,app_secret:BKASH_APP_SECRET})});
 const data=await r.json().catch(()=>({}));
 if(!r.ok||!data.id_token||data.statusCode&&String(data.statusCode)!=='0000')throw new Error(data.statusMessage||data.errorMessage||'bKash token request failed');
 bkashTokenCache={token:data.id_token,expiresAt:Date.now()+(Number(data.expires_in||3600)-60)*1000};
 return bkashTokenCache.token;
}
async function bkashCheckoutRequest(path,token,body){
 const r=await fetch(BKASH_BASE_URL+path,{method:'POST',headers:{accept:'application/json','content-type':'application/json',authorization:token,'x-app-key':BKASH_APP_KEY},body:JSON.stringify(body)});
 const data=await r.json().catch(()=>({}));
 if(!r.ok||data.statusCode&&String(data.statusCode)!=='0000')throw new Error(data.statusMessage||data.errorMessage||'bKash checkout request failed');
 return data;
}
function bkashCompleted(x){return String(x&&x.statusCode||'')==='0000'&&String(x&&x.transactionStatus||'').toLowerCase()==='completed'}

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
  const customerCode=String(req.query.customerCode||'').trim();
  let visiblePackages=packages;
  let allowPackageChoice=false;
  let currentPackage=null;
  if(customerCode){
   const customers=Array.isArray(state.data.customers)?state.data.customers:[];
   const customer=customers.find(x=>String(x.id||'')===customerCode)||customers.find(x=>String(x.clientCode||'').trim().toLowerCase()===customerCode.toLowerCase());
   if(!customer)return res.status(404).json({error:'Customer not found for this payment link'});
   allowPackageChoice=packageChoiceEnabled(customer);
   currentPackage={speed:String(customer.pkg||customer.packageName||customer.package||''),price:Number(customer.fee??customer.monthlyFee??customer.price??0),previousDue:Number(customer.prevDue??customer.previousDue??0)};
   if(!allowPackageChoice){
    const normalizePackageName=value=>String(value||'').trim().toLowerCase().replace(/\s+/g,' ').replace(/\s*mbps\s*$/i,'').trim();
    visiblePackages=packages.filter(p=>normalizePackageName(p.speed||p.name)===normalizePackageName(currentPackage.speed)&&Math.abs(Number(p.price??p.fee??0)-currentPackage.price)<0.01);
    // When package choice is OFF, the customer's saved package and fee are authoritative.
    // Do not block checkout just because the admin later renamed/removed that package.
    if(!visiblePackages.length&&currentPackage.speed&&Number.isFinite(currentPackage.price)&&currentPackage.price>0)visiblePackages=[currentPackage];
   }
  }
  const offers=Array.isArray(settings.offers)?settings.offers.filter(o=>o&&o.enabled===true&&String(o.text||'').trim()).map(o=>({id:String(o.id||''),text:String(o.text).trim(),enabled:true})):[];
  return send(res,{ok:true,companyName:settings.cloud&&settings.cloud.companyName||'',packages:visiblePackages,allowPackageChoice,currentPackage,merchantNumber:String(settings.merchantNumber||''),offers});
 }catch(e){return res.status(500).json({error:'Could not load company packages'})}
});
// Dedicated owner-only offer storage: do not rely on a full-device sync to keep offers.
app.get('/api/settings/offers',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Company owner access required'});
 const c=col('app_state');if(!c)return res.status(503).json({error:'Cloud database is not configured'});
 const state=await c.findOne({owner:ownerOf(req.user)});
 const settings=state&&state.data&&state.data.settings||{};
 const offers=Array.isArray(settings.offers)?settings.offers:[];
 return send(res,{ok:true,offers,updatedAt:state&&state.updatedAt||null});
});
app.put('/api/settings/offers',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Company owner access required'});
 const raw=req.body&&req.body.offers;
 if(!Array.isArray(raw))return res.status(400).json({error:'An offer list is required'});
 const offers=raw.map((o,i)=>({id:String(o&&o.id||('offer-'+Date.now()+'-'+i)),text:String(o&&o.text||'').trim(),enabled:o&&o.enabled===true,createdAt:String(o&&o.createdAt||new Date().toISOString()),updatedAt:new Date().toISOString()}));
 if(offers.some(o=>!o.text||o.text.length>500))return res.status(400).json({error:'Offer text is required and must be 500 characters or fewer'});
 const c=col('app_state');if(!c)return res.status(503).json({error:'Cloud database is not configured'});
 const owner=ownerOf(req.user),now=new Date().toISOString();
 // Persist offers independently so first-time cloud accounts can save them before a full sync.
 // Create a minimal state only when none exists; otherwise update just the offers field.
 const state=await c.findOne({owner});
 if(!state){
  await c.insertOne({owner,data:{customers:[],payments:[],expenses:[],pending:[],history:[],settings:{offers}},updatedAt:now});
 }else{
  await c.updateOne({owner},{$set:{'data.settings.offers':offers,updatedAt:now}});
 }
 return send(res,{ok:true,offers,updatedAt:now,message:'Offers saved'});
});
app.put('/api/settings/packages',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Company owner access required'});
 const raw=req.body&&req.body.packages;
 if(!Array.isArray(raw))return res.status(400).json({error:'A package list is required'});
 const packages=raw.map(p=>({speed:String(p&&p.speed||p&&p.name||'').trim(),price:Number((p&&p.price)??(p&&p.fee)??0)}));
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
// Company-owner managed sub-panel accounts. Sub-panels share only their owner's company data.
app.get('/api/subpanels',auth,async(req,res)=>{
 if(!isOwner(req.user)||isSystemAdmin(req.user))return res.status(403).json({error:'Company owner access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 try{
  const rows=await ac.find({owner:ownerOf(req.user),role:'worker'}).sort({createdAt:1}).project({passwordHash:0}).toArray();
  return send(res,{ok:true,accounts:rows.map(a=>({username:a.username,role:a.role,active:a.active!==false,permissions:Array.isArray(a.permissions)?a.permissions:['dashboard','customers','billing'],createdAt:a.createdAt||''}))});
 }catch(e){return res.status(500).json({error:'Could not load sub-panel accounts'})}
});
app.post('/api/subpanels',auth,async(req,res)=>{
 if(!isOwner(req.user)||isSystemAdmin(req.user))return res.status(403).json({error:'Company owner access required'});
 const username=String(req.body&&req.body.username||'').trim().toLowerCase();
 const password=String(req.body&&req.body.password||'');
 if(!/^[^\s@]+@gmail\.com$/i.test(username))return res.status(400).json({error:'Sub-panel login must be a valid Gmail address'});
 if(password.length<8)return res.status(400).json({error:'Sub-panel password must be at least 8 characters'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 try{
  if(await ac.findOne({username}))return res.status(409).json({error:'This Gmail is already registered'});
  const owner=ownerOf(req.user);
  const allowed=['dashboard','customers','billing','accounts','reports','sms'];
  const permissions=Array.isArray(req.body&&req.body.permissions)?[...new Set(req.body.permissions.map(String).filter(x=>allowed.includes(x)))]:['dashboard','customers','billing'];
  await ac.insertOne({username,email:username,passwordHash:bcrypt.hashSync(password,12),role:'worker',owner,permissions,active:true,approvalStatus:'approved',createdAt:new Date().toISOString()});
  return send(res,{ok:true,account:{username,role:'worker',active:true,permissions},message:'Sub-panel account created'});
 }catch(e){return res.status(500).json({error:'Could not create sub-panel account'})}
});
app.delete('/api/subpanels/:username',auth,async(req,res)=>{
 if(!isOwner(req.user)||isSystemAdmin(req.user))return res.status(403).json({error:'Company owner access required'});
 const username=String(req.params.username||'').trim().toLowerCase();
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 try{
  const result=await ac.deleteOne({username,owner:ownerOf(req.user),role:'worker'});
  if(!result.deletedCount)return res.status(404).json({error:'Sub-panel account not found'});
  return send(res,{ok:true,message:'Sub-panel account deleted'});
 }catch(e){return res.status(500).json({error:'Could not delete sub-panel account'})}
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

// Company presence: refreshed by signed-in company apps every 45 seconds.
app.post('/api/presence/heartbeat',auth,async(req,res)=>{
 if(isSystemAdmin(req.user))return send(res,{ok:true,systemAdmin:true});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const owner=String(req.user.owner||req.user.username||'').trim().toLowerCase();
 if(!owner)return res.status(400).json({error:'Company owner missing'});
 const account=await ac.findOne({username:owner});
 if(!account)return res.status(403).json({error:'Company account unavailable'});
 if(account.approvalStatus!=='approved'||account.active===false||account.accountStatus==='disabled')return res.status(403).json({error:'Company account is not active'});
 const now=new Date().toISOString();
 await ac.updateOne({username:owner},{$set:{lastSeenAt:now}});
 return send(res,{ok:true,lastSeenAt:now});
});

// System-admin controls for every company account.
app.get('/api/admin/companies',auth,async(req,res)=>{
 if(!isSystemAdmin(req.user))return res.status(403).json({error:'System administrator access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const accounts=await ac.find({$or:[{role:'owner'},{approvalStatus:{$exists:true}}]}).sort({createdAt:-1}).project({passwordHash:0}).toArray();
 send(res,{ok:true,companies:accounts.filter(a=>String(a.username||'')!==String(ADMIN_USER)).map(a=>({username:a.username,email:a.email||a.username,companyName:a.companyName||'',role:a.role||'owner',status:a.accountStatus==='disabled'?'disabled':(a.approvalStatus||((a.active===false)?'disabled':'approved')),active:a.active!==false&&a.accountStatus!=='disabled'&&a.approvalStatus!=='pending'&&a.approvalStatus!=='rejected',online:!!a.lastSeenAt&&(Date.now()-new Date(a.lastSeenAt).getTime()<120000)&&a.active!==false&&a.accountStatus!=='disabled'&&a.approvalStatus!=='pending'&&a.approvalStatus!=='rejected',lastSeenAt:a.lastSeenAt||'',disabledMessage:a.disabledMessage||'',createdAt:a.createdAt||''}))});
});
app.post('/api/admin/companies/:username/status',auth,async(req,res)=>{
 if(!isSystemAdmin(req.user))return res.status(403).json({error:'System administrator access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const u=String(req.params.username||'').trim().toLowerCase(), enabled=req.body&&req.body.enabled===true, message=String(req.body&&req.body.message||'').trim().slice(0,500);
 if(!u||u===String(ADMIN_USER).toLowerCase())return res.status(400).json({error:'Cannot change system administrator account'});
 const account=await ac.findOne({username:u});if(!account||account.role==='worker')return res.status(404).json({error:'Company account not found'});
 const fields=enabled?{accountStatus:'enabled',active:true,disabledMessage:'',updatedAt:new Date().toISOString()}:{accountStatus:'disabled',active:false,disabledMessage:message||'আপনার কোম্পানির অ্যাকাউন্ট প্রশাসক সাময়িকভাবে বন্ধ রেখেছেন। অনুগ্রহ করে STAR COMMUNICATION Admin-এর সঙ্গে যোগাযোগ করুন।',updatedAt:new Date().toISOString()};
 await ac.updateOne({username:u},{$set:fields});
 send(res,{ok:true,username:u,enabled,message:enabled?'Company account enabled':'Company account disabled',disabledMessage:fields.disabledMessage||''});
});

// System-admin feature switches for each company.
const ADMIN_FEATURES=['dashboard','customers','billing','collected','analytics','accounts','monitor','referrals','sms','packages','settings'];
app.get('/api/admin/companies/:username/features',auth,async(req,res)=>{
 if(!isSystemAdmin(req.user))return res.status(403).json({error:'System administrator access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const u=String(req.params.username||'').trim().toLowerCase();
 if(!u||u===String(ADMIN_USER).toLowerCase())return res.status(400).json({error:'Invalid company account'});
 const account=await ac.findOne({username:u});if(!account||account.role==='worker')return res.status(404).json({error:'Company account not found'});
 return send(res,{ok:true,username:u,features:Array.isArray(account.features)?account.features:ADMIN_FEATURES});
});
app.put('/api/admin/companies/:username/features',auth,async(req,res)=>{
 if(!isSystemAdmin(req.user))return res.status(403).json({error:'System administrator access required'});
 const ac=col(ACCOUNT_COLLECTION);if(!ac)return res.status(503).json({error:'Cloud database is not configured'});
 const u=String(req.params.username||'').trim().toLowerCase();
 if(!u||u===String(ADMIN_USER).toLowerCase())return res.status(400).json({error:'Invalid company account'});
 const account=await ac.findOne({username:u});if(!account||account.role==='worker')return res.status(404).json({error:'Company account not found'});
 const input=Array.isArray(req.body&&req.body.features)?req.body.features:[];
 const features=[...new Set(input.map(String).filter(x=>ADMIN_FEATURES.includes(x)))];
 await ac.updateOne({username:u},{$set:{features,featuresUpdatedAt:new Date().toISOString(),featuresUpdatedBy:req.user.username}});
 return send(res,{ok:true,username:u,features});
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
 const account=await ac.findOne({username:u,approvalStatus:'pending'});if(!account)return res.status(404).json({error:'Pending registration not found'});
 const result=await ac.updateOne({username:u,approvalStatus:'pending'},{$set:{active:true,approvalStatus:'approved',approvedAt:new Date().toISOString(),approvedBy:req.user.username}});
 if(!result.matchedCount)return res.status(404).json({error:'Pending registration not found'});
 let emailStatus={sent:false,reason:'No email address on registration'};try{emailStatus=await sendApprovalEmail(account.email||account.username,account.companyName||'Company')}catch(e){console.error('Approval email failed:',e.message);emailStatus={sent:false,reason:'Email send failed; check SMTP configuration'}}
 send(res,{ok:true,message:'Registration approved',username:u,emailSent:emailStatus.sent,emailMessage:emailStatus.sent?'Approval email sent':'Account approved; email notification not sent. '+emailStatus.reason});
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
 const u=String(username||'').trim().toLowerCase(), p=String(password||'');
 if(!u||!p)return res.status(400).json({error:'Username and password are required'});
 try{
  // The configured system administrator must always receive the system-admin role,
  // even if an older account document exists with a stale role value.
  if(ADMIN_USER&&u===String(ADMIN_USER).trim().toLowerCase()){
   if(!ADMIN_HASH||!bcrypt.compareSync(p,ADMIN_HASH))return res.status(401).json({error:'Invalid system administrator credentials'});
   const token=jwt.sign({username:u,role:'owner',owner:u},JWT_SECRET,{expiresIn:'30d'});
   return send(res,{token,expiresIn:30*24*60*60,role:'owner',owner:u,username:u,permissions:['dashboard','customers','billing','accounts','reports','sms'],features:['dashboard','customers','billing','collected','analytics','accounts','monitor','referrals','sms','packages','settings'],systemAdmin:true});
  }
  let account=null;
  const ac=col(ACCOUNT_COLLECTION);  if(ac)account=await ac.findOne({username:u});  if(account){
   if(!bcrypt.compareSync(p,account.passwordHash))return res.status(401).json({error:'Invalid username or password'});
   if(account.accountStatus==='disabled')return res.status(403).json({error:String(account.disabledMessage||'এই কোম্পানির অ্যাকাউন্ট প্রশাসক সাময়িকভাবে বন্ধ রেখেছেন। অনুগ্রহ করে STAR COMMUNICATION Admin-এর সঙ্গে যোগাযোগ করুন।').slice(0,500)});
   if(account.approvalStatus==='pending'||account.active===false)return res.status(403).json({error:'Your registration is pending administrator approval'});
   if(account.approvalStatus==='rejected')return res.status(403).json({error:String(account.disabledMessage||'Your registration was not approved. Contact the administrator').slice(0,500)});
   const claims={username:account.username,role:account.role||'worker',owner:account.owner||account.username,permissions:Array.isArray(account.permissions)?account.permissions:(account.role==='worker'?['dashboard','customers','billing']:['dashboard','customers','billing','accounts','reports','sms'])};
   const token=jwt.sign(claims,JWT_SECRET,{expiresIn:'30d'});
   return send(res,{token,expiresIn:30*24*60*60,role:claims.role,owner:claims.owner,username:claims.username,permissions:claims.permissions,features:Array.isArray(account.features)?account.features:['dashboard','customers','billing','collected','analytics','accounts','monitor','referrals','sms','packages','settings']});
  }
  return res.status(401).json({error:'Invalid username or password'});
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
   customers:data.customers.map(c=>({...c,allowPackageChoice:flagEnabled(c.allowPackageChoice)||flagEnabled(c.allowPackageChange),allowPackageChange:flagEnabled(c.allowPackageChoice)||flagEnabled(c.allowPackageChange)})),
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
   // Offers are managed through /api/settings/offers. Preserve the canonical cloud list during normal device sync,
   // because older/local app state may not contain offers and must never erase offers before a payment link opens.
   if(existing.data.settings&&Array.isArray(existing.data.settings.offers)){
     clean.settings.offers=existing.data.settings.offers;
   }
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

app.post('/api/bkash/create',async(req,res)=>{
 try{
  const body=req.body||{};
  const owner=String(body.company||'').trim().toLowerCase();
  const customerCode=String(body.customerCode||'').trim();
  const selectedPackage=String(body.selectedPackage||'').trim();
  const packagePrice=Number(body.packagePrice||0);
  const requestedAmount=Number(body.amount||0);
  if(!owner||!customerCode||!selectedPackage||!Number.isFinite(packagePrice)||packagePrice<=0)return res.status(400).json({error:'Company, customer and selected package are required'});
  const stateCol=col('app_state');if(!stateCol)return res.status(503).json({error:'Cloud database is not configured'});
  const state=await stateCol.findOne({owner});
  if(!state||!state.data)return res.status(404).json({error:'Company cloud data was not found'});
  const customer=(state.data.customers||[]).find(c=>String(c.id)===customerCode);
  if(!customer)return res.status(404).json({error:'Customer does not belong to this company'});
  const packages=Array.isArray(state.data.settings&&state.data.settings.packages)?state.data.settings.packages:[];
  const assignedPackage=String(customer.pkg||customer.packageName||'').trim();
  const assignedPrice=Number(customer.fee??customer.monthlyFee??0);
  // Enforce the package-choice permission on the server, not only in the page UI.
  const packageChoiceAllowed=packageChoiceEnabled(customer);
   if(!packageChoiceAllowed){
   if(!assignedPackage||!Number.isFinite(assignedPrice)||assignedPrice<=0)return res.status(409).json({error:'Customer package is not configured correctly'});
   if(selectedPackage!==assignedPackage||Math.abs(packagePrice-assignedPrice)>0.01)return res.status(403).json({error:'Package choice is locked. This customer can only pay for the assigned package'});
  }
  const normalizePackageName=value=>String(value||'').trim().toLowerCase().replace(/\s+/g,' ').replace(/\s*mbps\s*$/i,'');
  const livePackage=packages.find(p=>normalizePackageName(p.speed||p.name)===normalizePackageName(selectedPackage));
  if(packageChoiceAllowed&&(!livePackage||Math.abs(Number(livePackage.price??livePackage.fee??0)-packagePrice)>0.01))return res.status(409).json({error:'The selected package is not current. Please refresh the page and try again.'});
  // When package choice is locked, the customer's saved package price is authoritative.
  // A stale or changed package catalogue must not prevent payment of that assigned bill.
  const previousDue=Math.max(0,Number(customer.prevDue??customer.previousDue??0));
  const amount=Number((packagePrice+previousDue).toFixed(2));
  if(!Number.isFinite(requestedAmount)||Math.abs(requestedAmount-amount)>0.01)return res.status(409).json({error:'Payment amount does not match the current package and previous due'});
  const token=await getBkashToken();
  const invoice=String('SC-'+customerCode+'-'+Date.now()).replace(/[^A-Za-z0-9_-]/g,'').slice(0,50);
  const created=await bkashCheckoutRequest('/checkout/payment/create',token,{mode:'0011',payerReference:customerCode,callbackURL:PUBLIC_URL+'/api/bkash/callback',amount:amount.toFixed(2),currency:'BDT',intent:'sale',merchantInvoiceNumber:invoice});
  if(!created.paymentID||!created.bkashURL)throw new Error('bKash did not return a checkout URL');
  await db.collection('bkash_checkout_sessions').insertOne({paymentID:String(created.paymentID),owner,customerCode,customerName:String(customer.name||body.customerName||'Customer'),customerMobile:String(customer.phone||body.customerMobile||''),selectedPackage,packagePrice,previousDue,amount,invoice,status:'PENDING',createdAt:new Date().toISOString()});
  return send(res,{ok:true,paymentID:created.paymentID,bkashURL:created.bkashURL,merchantInvoiceNumber:invoice});
 }catch(e){return res.status(502).json({error:String(e.message||'Unable to start bKash payment').slice(0,220)})}
});
app.get('/api/bkash/status',async(req,res)=>{
 const paymentID=String(req.query.paymentID||'').trim();
 if(!paymentID)return res.status(400).json({error:'paymentID is required'});
 const c=col('bkash_checkout_sessions');if(!c)return res.status(503).json({error:'Cloud database is not configured'});
 const session=await c.findOne({paymentID});
 if(!session)return res.status(404).json({ok:true,verified:false,status:'NOT_FOUND'});
 return send(res,{ok:true,verified:session.status==='PAID',status:session.status||'PENDING',customerCode:session.customerCode});
});
app.get('/api/bkash/callback',async(req,res)=>{
 const paymentID=String(req.query.paymentID||'').trim(), status=String(req.query.status||'');
 const page=(result)=>res.redirect(PAYMENT_PAGE_URL+'?status='+encodeURIComponent(result)+(paymentID?'&paymentID='+encodeURIComponent(paymentID):'')+'&api='+encodeURIComponent(PUBLIC_URL));
 if(!paymentID)return page('invalid');
 const sessions=col('bkash_checkout_sessions');if(!sessions)return page('failed');
 try{
  const session=await sessions.findOne({paymentID});
  if(!session)return page('invalid');
  if(session.status==='PAID')return page('success');
  if(status==='cancel'||status==='failure'){await sessions.updateOne({paymentID},{$set:{status:status==='cancel'?'CANCELLED':'FAILED',updatedAt:new Date().toISOString()}});return page(status==='cancel'?'cancelled':'failed')}
  const token=await getBkashToken();
  const result=await bkashCheckoutRequest('/checkout/payment/execute',token,{paymentID});
  if(!bkashCompleted(result))throw new Error(result.statusMessage||'bKash did not confirm a completed payment');
  if(Math.abs(Number(result.amount||0)-Number(session.amount||0))>0.01)throw new Error('Verified payment amount does not match the requested amount');
  const trxID=String(result.trxID||'');
  const stateCol=col('app_state'),state=await stateCol.findOne({owner:session.owner});
  if(!state||!state.data)throw new Error('Company data not found after payment verification');
  const data=state.data,customers=Array.isArray(data.customers)?data.customers:[],customer=customers.find(c=>String(c.id)===String(session.customerCode));
  if(!customer)throw new Error('Customer not found after payment verification');
  const payments=Array.isArray(data.payments)?data.payments:(data.payments=[]);
  const duplicate=payments.some(p=>String(p.ref||'')===trxID||String(p.paymentID||'')===paymentID);
  const now=new Date(),iso=now.toISOString();
  customer.pkg=session.selectedPackage;  customer.fee=Number(session.packagePrice);
  customer.prevDue=0;  if(!duplicate)payments.push({id:'bkash-'+paymentID,customer:String(session.customerCode),amount:Number(session.amount),date:iso.slice(0,10),month:iso.slice(0,7),status:'paid',source:'bkash',ref:trxID||paymentID,paymentID,createdAt:iso,updatedAt:iso});
  await stateCol.updateOne({owner:session.owner},{$set:{data,updatedAt:iso}});
  await sessions.updateOne({paymentID},{$set:{status:'PAID',trxID,verifiedAmount:Number(result.amount),verifiedAt:iso,updatedAt:iso}});
  return page('success');
 }catch(e){
  await sessions.updateOne({paymentID},{$set:{status:'FAILED',verificationError:String(e.message||'verification failed').slice(0,200),updatedAt:new Date().toISOString()}}).catch(()=>{});
  return page('failed');
 }
});

app.get('/api/bkash/transactions',auth,async(req,res)=>send(res,await list('bkash',ownerOf(req.user))));
app.post('/api/bkash/transactions',auth,async(req,res)=>send(res,await insert('bkash',{id:Date.now(),...req.body,status:'PENDING',createdAt:new Date().toISOString()},ownerOf(req.user))));
app.post('/api/bkash/transactions/:id/manual-paid',auth,async(req,res)=>{await update('bkash',req.params.id,{status:'MANUAL_MATCHED',matchedCustomerId:req.body.customerId},ownerOf(req.user));send(res,{ok:true})});
app.post('/api/bkash/transactions/:id/cancel',auth,async(req,res)=>{await update('bkash',req.params.id,{status:'CANCELLED'},ownerOf(req.user));send(res,{ok:true})});

function sshExec({host,port,user,password,command,timeout=12000}){return new Promise((resolve,reject)=>{const c=new SSHClient();let out='',err='';const timer=setTimeout(()=>{c.end();reject(new Error('OLT SSH timeout'))},timeout);c.on('ready',()=>c.exec(command,(e,s)=>{if(e){clearTimeout(timer);c.end();return reject(e)}s.on('data',d=>out+=d.toString());s.stderr.on('data',d=>err+=d.toString());s.on('close',()=>{clearTimeout(timer);c.end();resolve({out,err})})})).on('error',e=>{clearTimeout(timer);reject(e)}).connect({host,port:Number(port||22),username:user,password,readyTimeout:timeout,hostVerifier:()=>true})})}
function vsolSshExec({host,port,user,password,command,timeout=18000}){
 const allowed=new Set(['show version','show onu status all','show running-config']);
 if(!allowed.has(String(command||'').trim().toLowerCase()))return Promise.reject(new Error('Only approved read-only VSOL commands are allowed'));
 return new Promise((resolve,reject)=>{
  const c=new SSHClient();let out='',err='',stage='start',done=false,commandSent=false;
  const timer=setTimeout(()=>finish(new Error('VSOL SSH timeout')),timeout);
  const finish=(e)=>{if(done)return;done=true;clearTimeout(timer);try{c.end()}catch{};e?reject(e):resolve({out,err})};
  c.on('ready',()=>c.shell({term:'vt100'},(e,stream)=>{
   if(e)return finish(e);
   const write=x=>{try{stream.write(x+'\n')}catch(error){finish(error)}};
   stream.on('data',d=>{
    out+=d.toString();const tail=out.slice(-1400);
    if(stage==='start'&&/(?:login|username)\s*[:>]\s*$/i.test(tail)){write(user);stage='login';return}
    if((stage==='start'||stage==='login'||stage==='enable')&&/password\s*[:>]\s*$/i.test(tail)){write(password);stage='password';return}
    if(stage==='start'&&/>\s*$/.test(tail)){write('enable');stage='enable';return}
    // A privileged # prompt is already in EXEC mode: never enter configuration mode.
    if(!commandSent&&(stage==='start'||stage==='login'||stage==='password'||stage==='enable')&&/#\s*$/.test(tail)){
     write(command);commandSent=true;stage='command';return;
    }
    if(stage==='command'&&/\n[^\r\n]{0,100}[#>]\s*$/.test(tail)){setTimeout(()=>finish(),700)}
   });
   stream.stderr?.on('data',d=>err+=d.toString());
   stream.on('close',()=>finish());
  })).on('error',e=>finish(e)).connect({host,port:Number(port||22),username:user,password,readyTimeout:timeout,hostVerifier:()=>true});
 });
}

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

// Read-only SNMP interface traffic. Rates are calculated from two counter samples.
// Does not write to or configure the OLT.
const snmp=require('net-snmp');
const oltTrafficSamples=new Map();
function snmpWalkTable(session,oid){
 return new Promise((resolve,reject)=>{
  const values=[];
  session.subtree(oid,20,(varbinds)=>{
   for(const vb of varbinds||[]){
    if(snmp.isVarbindError(vb)){reject(new Error(snmp.varbindError(vb)));return}
    values.push({oid:vb.oid,value:vb.value});
   }
  },err=>err?reject(err):resolve(values));
 });
}
function oidIndex(oid,base){return String(oid).startsWith(base+'.')?String(oid).slice(base.length+1):null}
app.post('/api/olt/traffic',auth,async(req,res)=>{
 const {host,community='public'}=req.body||{};
 if(!host)return res.status(400).json({error:'OLT IP is required'});
 if(typeof community!=='string'||!community||community.length>128)return res.status(400).json({error:'Valid read-only SNMP community is required'});
 let session;
 try{
  session=snmp.createSession(host,community,{version:snmp.Version2c,timeout:3500,retries:0,transport:'udp4'});
  const bases={name:'1.3.6.1.2.1.31.1.1.1.1',in64:'1.3.6.1.2.1.31.1.1.1.6',out64:'1.3.6.1.2.1.31.1.1.1.10',in32:'1.3.6.1.2.1.2.2.1.10',out32:'1.3.6.1.2.1.2.2.1.16'};
  const [names,ins64,outs64,ins32,outs32]=await Promise.all([
   snmpWalkTable(session,bases.name),snmpWalkTable(session,bases.in64),snmpWalkTable(session,bases.out64),snmpWalkTable(session,bases.in32),snmpWalkTable(session,bases.out32)
  ]);
  const mapByIndex=(arr,base)=>new Map(arr.map(x=>[oidIndex(x.oid,base),x.value]));
  const nm=mapByIndex(names,bases.name),i64=mapByIndex(ins64,bases.in64),o64=mapByIndex(outs64,bases.out64),i32=mapByIndex(ins32,bases.in32),o32=mapByIndex(outs32,bases.out32);
  const now=Date.now(),key=String(host),prev=oltTrafficSamples.get(key)||new Map(),next=new Map();
  const interfaces=[];
  for(const [idx,rawName] of nm){
   const name=Buffer.isBuffer(rawName)?rawName.toString():String(rawName);
   const inRaw=i64.get(idx)??i32.get(idx),outRaw=o64.get(idx)??o32.get(idx);
   if(inRaw==null||outRaw==null)continue;
   const inbound=BigInt(inRaw.toString()),outbound=BigInt(outRaw.toString());
   const old=prev.get(idx);let inMbps=null,outMbps=null;
   if(old&&now>old.time&&inbound>=old.inbound&&outbound>=old.outbound){
    const sec=(now-old.time)/1000;
    inMbps=Number((inbound-old.inbound)*8n)/sec/1000000;
    outMbps=Number((outbound-old.outbound)*8n)/sec/1000000;
   }
   next.set(idx,{inbound,outbound,time:now});
   interfaces.push({index:idx,name,downloadMbps:inMbps,uploadMbps:outMbps,totalInBytes:inbound.toString(),totalOutBytes:outbound.toString()});
  }
  oltTrafficSamples.set(key,next);
  const rates=interfaces.filter(x=>x.downloadMbps!=null&&x.uploadMbps!=null);
  res.json({ok:true,connected:true,method:'SNMPv2c read-only IF-MIB',sampleReady:rates.length>0,updatedAt:new Date(now).toISOString(),downloadMbps:rates.reduce((a,x)=>a+x.downloadMbps,0),uploadMbps:rates.reduce((a,x)=>a+x.uploadMbps,0),interfaces});
 }catch(e){
  res.status(502).json({error:'SNMP traffic read failed. Check SNMP reachability/community and server network access. '+(e.message||e)});
 }finally{try{session?.close()}catch{}}
});

app.post('/api/olt/system',auth,async(req,res)=>{
 const {host,community='public'}=req.body||{};
 if(!host)return res.status(400).json({error:'OLT IP is required'});
 if(typeof community!=='string'||!community||community.length>128)return res.status(400).json({error:'Valid read-only SNMP community is required'});
 let session;
 try{
  session=snmp.createSession(host,community,{version:snmp.Version2c,timeout:3500,retries:0,transport:'udp4'});
  const get=(oid)=>new Promise((resolve,reject)=>session.get([oid],(err,varbinds)=>{if(err)return reject(err);const v=varbinds&&varbinds[0];if(!v||snmp.isVarbindError(v))return reject(new Error(v?snmp.varbindError(v):'SNMP value unavailable'));resolve(v.value)}));
  const walk=(base)=>snmpWalkTable(session,base);
  const [descr,uptime,ifNames,ifStatuses,ifSpeeds]=await Promise.all([
   get('1.3.6.1.2.1.1.1.0').catch(()=>null),
   get('1.3.6.1.2.1.1.3.0').catch(()=>null),
   walk('1.3.6.1.2.1.31.1.1.1.1').catch(()=>[]),
   walk('1.3.6.1.2.1.2.2.1.8').catch(()=>[]),
   walk('1.3.6.1.2.1.2.2.1.5').catch(()=>[])
  ]);
  const idx=(x,base)=>oidIndex(x.oid,base), names=new Map(ifNames.map(x=>[idx(x,'1.3.6.1.2.1.31.1.1.1.1'),Buffer.isBuffer(x.value)?x.value.toString():String(x.value)])), statuses=new Map(ifStatuses.map(x=>[idx(x,'1.3.6.1.2.1.2.2.1.8'),Number(x.value)])), speeds=new Map(ifSpeeds.map(x=>[idx(x,'1.3.6.1.2.1.2.2.1.5'),Number(x.value)]));
  const interfaces=[...names].map(([index,name])=>({index,name,linkStatus:({1:'UP',2:'DOWN',3:'TESTING',4:'UNKNOWN',5:'DORMANT',6:'NOT_PRESENT',7:'LOWER_LAYER_DOWN'})[statuses.get(index)]||'UNKNOWN',ifOperStatus:statuses.get(index)??null,speedMbps:speeds.has(index)?speeds.get(index)/1000000:null}));
  res.json({ok:true,connected:true,method:'SNMPv2c read-only IF-MIB',systemDescription:descr==null?null:(Buffer.isBuffer(descr)?descr.toString():String(descr)),uptimeTicks:uptime==null?null:String(uptime),uptimeSeconds:uptime==null?null:Math.floor(Number(uptime)/100),interfaceCount:interfaces.length,interfaces,updatedAt:new Date().toISOString()});
 }catch(e){res.status(502).json({ok:false,connected:false,error:'OLT system/uplink SNMP read failed: '+(e.message||e)+'. Check that UDP/161 and the read-only SNMP community are enabled and reachable from the backend.'})}
 finally{try{session?.close()}catch{}}
});

function oltFailureReason(err,host,port,protocol){
 const m=String(err&&err.message||err||'Unknown error');
 const h=String(host||'');
 const privateIp=/^(10\\.|192\\.168\\.|172\\.(1[6-9]|2[0-9]|3[01])\\.)/.test(h);
 if((/timeout|ETIMEDOUT|EHOSTUNREACH|ENETUNREACH/i.test(m))&&privateIp&&process.env.RENDER){
  return 'OLT management IP '+h+' is private and this backend is running on Render, which cannot directly route to your LAN. Use a secure site-to-site VPN or a local LAN connector/agent. Also verify OLT power, VLAN, firewall and management port '+Number(port||(String(protocol).toLowerCase()==='telnet'?23:22))+'. Original error: '+m;
 }
 if(/timeout|ETIMEDOUT/i.test(m))return 'Connection timeout to '+h+':'+Number(port||(String(protocol).toLowerCase()==='telnet'?23:22))+'. Possible causes: OLT power loss, wrong management IP/port, uplink or route down, firewall, or SSH/Telnet disabled. A timeout alone cannot identify which cause occurred. '+m;
 if(/ECONNREFUSED/i.test(m))return 'OLT host responded but refused port '+Number(port||22)+'. Enable the selected SSH/Telnet service or correct the port. '+m;
 if(/authentication|password|permission|denied/i.test(m))return 'OLT authentication/CLI permission failed. Check the account and password. '+m;
 return m;
}
app.post('/api/olt/test',auth,async(req,res)=>{const {host,port,protocol,user,password,vendor}=req.body||{};if(!host||!user||!password)return res.status(400).json({error:'OLT IP, username and password are required'});try{const cmd=commandFor(vendor,'version');const r=await runOltCommand({host,port,user,password,protocol,vendor,command:cmd});send(res,{ok:true,connected:true,protocol:protocol||'ssh',vendor:vendor||'generic',output:r.out.slice(-8000)})}catch(e){res.status(502).json({ok:false,connected:false,reasonCode:/timeout|ETIMEDOUT/i.test(String(e.message))?'TIMEOUT':/ECONNREFUSED/i.test(String(e.message))?'PORT_CLOSED':/authentication|password|denied/i.test(String(e.message))?'AUTH_FAILED':'UNREACHABLE',error:'OLT connection failed: '+oltFailureReason(e,host,port,protocol)})}});
app.post('/api/olt/monitor',auth,async(req,res)=>{const {host,port,protocol,user,password,vendor}=req.body||{};if(!host||!user||!password)return res.status(400).json({error:'OLT IP, username and password are required'});try{const cmd=commandFor(vendor,'summary');const r=await runOltCommand({host,port,user,password,protocol,vendor,command:cmd});const counts=parseOnuCounts(r.out,vendor);send(res,{ok:true,connected:true,vendor:vendor||'generic',raw:r.out.slice(-15000),...counts,parser:'heuristic'})}catch(e){res.status(502).json({ok:false,connected:false,reasonCode:/timeout|ETIMEDOUT/i.test(String(e.message))?'TIMEOUT':/ECONNREFUSED/i.test(String(e.message))?'PORT_CLOSED':/authentication|password|denied/i.test(String(e.message))?'AUTH_FAILED':'UNREACHABLE',error:'OLT monitor failed: '+oltFailureReason(e,host,port,protocol)})}});
app.post('/api/olt/onu-list',auth,async(req,res)=>{const {host,port,protocol,user,password,vendor}=req.body||{};if(!host||!user||!password)return res.status(400).json({error:'OLT IP, username and password are required'});if(String(vendor||'').toLowerCase()!=='vsol')return res.status(400).json({error:'Live ONU list is currently implemented for VSOL EPON'});try{const r=await runOltCommand({host,port, user,password,protocol,vendor,command:'show onu status all'});const rows=parseVsolOnuRows(r.out);const counts=parseOnuCounts(r.out,'vsol');send(res,{ok:true,connected:true,vendor:'vsol',rows,...counts,raw:r.out.slice(-20000)})}catch(e){res.status(502).json({ok:false,connected:false,reasonCode:/timeout|ETIMEDOUT/i.test(String(e.message))?'TIMEOUT':/ECONNREFUSED/i.test(String(e.message))?'PORT_CLOSED':/authentication|password|denied/i.test(String(e.message))?'AUTH_FAILED':'UNREACHABLE',error:'VSOL ONU list failed: '+oltFailureReason(e,host,port,protocol)})}});
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

function integrationEncryptionKey(){
 const raw=String(process.env.COMPANY_INTEGRATION_ENCRYPTION_KEY||'');
 if(raw.length<32)throw new Error('COMPANY_INTEGRATION_ENCRYPTION_KEY must be configured with at least 32 characters');
 return crypto.createHash('sha256').update(raw).digest();
}
function encryptIntegrationSecret(value){
 const iv=crypto.randomBytes(12),cipher=crypto.createCipheriv('aes-256-gcm',integrationEncryptionKey(),iv);
 const data=Buffer.concat([cipher.update(String(value),'utf8'),cipher.final()]);
 return {iv:iv.toString('base64'),tag:cipher.getAuthTag().toString('base64'),data:data.toString('base64')};
}
function decryptIntegrationSecret(box){
 if(!box||!box.iv||!box.tag||!box.data)return '';
 const decipher=crypto.createDecipheriv('aes-256-gcm',integrationEncryptionKey(),Buffer.from(box.iv,'base64'));
 decipher.setAuthTag(Buffer.from(box.tag,'base64'));
 return Buffer.concat([decipher.update(Buffer.from(box.data,'base64')),decipher.final()]).toString('utf8');
}
async function getBaniqCredentials(owner){
 const c=col('company_integrations');
 if(!c)throw new Error('Cloud database is not configured');
 const row=await c.findOne({owner:String(owner)});
 const baniq=row&&row.baniq||{};
 return {keyId:String(baniq.keyId||''),secret:decryptIntegrationSecret(baniq.secret)};
}
app.get('/api/integrations/baniq/settings',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Company owner access required'});
 try{
  const c=col('company_integrations');if(!c)return res.status(503).json({error:'Cloud database is not configured'});
  const row=await c.findOne({owner:ownerOf(req.user)});
  const cfg=row&&row.baniq||{};
  return send(res,{ok:true,configured:!!(cfg.keyId&&cfg.secret&&cfg.secret.data),keyId:cfg.keyId||'',apiBase:(process.env.BANIQ_API_BASE||'https://api.baniq.app').replace(/\/$/,'')});
 }catch(e){return res.status(503).json({error:String(e.message||'Could not read Baniq settings').slice(0,160)})}
});
app.put('/api/integrations/baniq/settings',auth,async(req,res)=>{
 if(!isOwner(req.user))return res.status(403).json({error:'Company owner access required'});
 const keyId=String(req.body&&req.body.keyId||'').trim(),secret=String(req.body&&req.body.secret||'');
 if(!keyId||keyId.length>200||!secret||secret.length>1000)return res.status(400).json({error:'Baniq API Key ID and API Secret are required'});
 try{
  const c=col('company_integrations');if(!c)return res.status(503).json({error:'Cloud database is not configured'});
  const owner=ownerOf(req.user),now=new Date().toISOString();
  const encrypted=encryptIntegrationSecret(secret);
  await c.updateOne({owner},{$set:{owner,baniq:{keyId,secret:encrypted,updatedAt:now},updatedAt:now}},{upsert:true});
  return send(res,{ok:true,configured:true,keyId,message:'Baniq credentials encrypted and saved for this company only'});
 }catch(e){return res.status(503).json({error:String(e.message||'Could not save Baniq settings').slice(0,180)})}
});

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

require('./baniq-integration')(app,{col,ownerOf,PUBLIC_URL, PAYMENT_PAGE_URL, integrationSettings, callConfiguredApi, getBaniqCredentials});

app.listen(PORT,'0.0.0.0',async()=>{try{await initDb();console.log('STAR COMMUNICATION server on '+PORT+' at 0.0.0.0')}catch(e){console.error(e);process.exit(1)}});