const express=require('express');
const cors=require('cors');
require('dotenv').config();
const {sendPaymentSms}=require('./sms-notifier');

const app=express();
app.use(cors());
app.use(express.json({limit:'100kb'}));

const PORT=process.env.PORT||10000;
const BKASH_BASE_URL=(process.env.BKASH_BASE_URL||'https://checkout.sandbox.bka.sh/v1.2.0-beta').replace(/\/$/,'');
const BKASH_APP_KEY=process.env.BKASH_APP_KEY||'';
const BKASH_APP_SECRET=process.env.BKASH_APP_SECRET||'';
const BKASH_USERNAME=process.env.BKASH_USERNAME||'';
const BKASH_PASSWORD=process.env.BKASH_PASSWORD||'';
const PUBLIC_URL=(process.env.PUBLIC_URL||'').replace(/\/$/,'');
const PAYMENT_PAGE_URL=process.env.PAYMENT_PAGE_URL||'https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html';
let tokenCache={id_token:'',expiresAt:0};
const sessions=new Map();

function requireConfig(){
  if(!BKASH_APP_KEY||!BKASH_APP_SECRET||!BKASH_USERNAME||!BKASH_PASSWORD)throw new Error('bKash credentials are not configured');
  if(!PUBLIC_URL)throw new Error('PUBLIC_URL is not configured');
}
async function bkashFetch(path,options={}){
  const r=await fetch(BKASH_BASE_URL+path,{...options,headers:{accept:'application/json','content-type':'application/json',...(options.headers||{})}});
  const data=await r.json().catch(()=>({}));
  if(!r.ok||data.statusCode&&data.statusCode!=='0000')throw new Error(data.statusMessage||data.errorMessage||`bKash HTTP ${r.status}`);
  return data;
}
async function getToken(){
  requireConfig();
  if(tokenCache.id_token&&Date.now()<tokenCache.expiresAt)return tokenCache.id_token;
  const data=await bkashFetch('/checkout/token/grant',{method:'POST',headers:{username:BKASH_USERNAME,password:BKASH_PASSWORD},body:JSON.stringify({app_key:BKASH_APP_KEY,app_secret:BKASH_APP_SECRET})});
  tokenCache={id_token:data.id_token,expiresAt:Date.now()+(Number(data.expires_in||3600)-60)*1000};
  return tokenCache.id_token;
}
function success(data){return String(data?.statusCode||'')==='0000'&&String(data?.transactionStatus||'Completed').toLowerCase()==='completed'}

app.get('/api/health',(req,res)=>res.json({ok:true,service:'STAR COMMUNICATION bKash API',sandbox:BKASH_BASE_URL.includes('sandbox'),smsConfigured:!!(process.env.SMS_API_URL&&process.env.SMS_API_KEY)}));

app.post('/api/bkash/create',async(req,res)=>{
  try{
    const {customerCode,customerName,customerMobile,amount,merchantInvoiceNumber}=req.body||{};
    const value=Number(amount);
    if(!customerCode||!Number.isFinite(value)||value<=0)return res.status(400).json({error:'customerCode and a valid amount are required'});
    const token=await getToken();
    const invoice=String(merchantInvoiceNumber||`SC-${customerCode}-${Date.now()}`).replace(/[^A-Za-z0-9_-]/g,'').slice(0,50);
    const callback=`${PUBLIC_URL}/api/bkash/callback`;
    const data=await bkashFetch('/checkout/payment/create',{method:'POST',headers:{authorization:token,'x-app-key':BKASH_APP_KEY},body:JSON.stringify({mode:'0011',payerReference:String(customerCode),callbackURL:callback,amount:value.toFixed(2),currency:'BDT',intent:'sale',merchantInvoiceNumber:invoice})});
    sessions.set(String(data.paymentID),{customerCode:String(customerCode),customerName:String(customerName||'Customer'),customerMobile:String(customerMobile||''),amount:value,invoice});
    res.json({ok:true,paymentID:data.paymentID,bkashURL:data.bkashURL,merchantInvoiceNumber:invoice});
  }catch(e){res.status(502).json({error:e.message||'bKash create payment failed'})}
});

async function executePayment(paymentID){
  const token=await getToken();
  return bkashFetch('/checkout/payment/execute',{method:'POST',headers:{authorization:token,'x-app-key':BKASH_APP_KEY},body:JSON.stringify({paymentID})});
}

app.get('/api/bkash/callback',async(req,res)=>{
  const paymentID=String(req.query.paymentID||'');
  const status=String(req.query.status||'');
  if(!paymentID)return res.redirect(`${PAYMENT_PAGE_URL}?status=invalid`);
  try{
    if(status==='cancel'||status==='failure')return res.redirect(`${PAYMENT_PAGE_URL}?status=${encodeURIComponent(status)}&paymentID=${encodeURIComponent(paymentID)}`);
    const data=await executePayment(paymentID);
    if(!success(data))throw new Error(data.statusMessage||'bKash payment was not completed');
    const s=sessions.get(paymentID)||{};
    let sms={sent:false,reason:'customer_mobile_missing'};
    if(s.customerMobile){
      try{sms=await sendPaymentSms({mobile:s.customerMobile,customerCode:s.customerCode,customerName:s.customerName,amount:Number(data.amount||s.amount||0),transactionId:data.trxID||paymentID});}
      catch(e){sms={sent:false,reason:e.message||'sms_failed'};console.error('Payment SMS failed:',e.message)}
    }
    sessions.set(paymentID,{...s,verified:true,trxID:data.trxID||'',sms});
    const url=`${PAYMENT_PAGE_URL}?status=success&paymentID=${encodeURIComponent(paymentID)}&trxID=${encodeURIComponent(data.trxID||'')}&code=${encodeURIComponent(s.customerCode||'')}&name=${encodeURIComponent(s.customerName||'Customer')}&amount=${encodeURIComponent(data.amount||s.amount||'')}&sms=${encodeURIComponent(sms.sent?'sent':'pending')}`;
    res.redirect(url);
  }catch(e){console.error('bKash callback:',e.message);res.redirect(`${PAYMENT_PAGE_URL}?status=error&paymentID=${encodeURIComponent(paymentID)}`)}
});

app.post('/api/bkash/execute',async(req,res)=>{
  try{
    const paymentID=String(req.body?.paymentID||'');
    if(!paymentID)return res.status(400).json({error:'paymentID is required'});
    const data=await executePayment(paymentID);
    if(!success(data))return res.status(400).json(data);
    const s=sessions.get(paymentID)||{};
    let sms={sent:false,reason:'customer_mobile_missing'};
    if(s.customerMobile){try{sms=await sendPaymentSms({mobile:s.customerMobile,customerCode:s.customerCode,customerName:s.customerName,amount:Number(data.amount||s.amount||0),transactionId:data.trxID||paymentID});}catch(e){sms={sent:false,reason:e.message||'sms_failed'}}}
    sessions.set(paymentID,{...s,verified:true,trxID:data.trxID||'',sms});
    res.json({...data,verified:true,sms});
  }catch(e){res.status(502).json({error:e.message||'bKash execute failed'})}
});

app.listen(PORT,()=>console.log(`STAR COMMUNICATION bKash API on ${PORT}`));
