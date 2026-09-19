from pathlib import Path
import re

HTML=Path("app/src/main/assets/index.html")
s=HTML.read_text(encoding="utf-8")
D=chr(36)

if "function customerPaymentLink(id)" not in s:
    if "Details</button>" not in s: raise SystemExit("customer Details button not found")
    add = '<button class="small view" onclick="sendOneSms(' + chr(39) + chr(36) + '{c.phone}' + chr(39) + ',' + chr(39) + chr(36) + '{esc(c.name)}' + chr(39) + ')">📩 SMS</button><button class="small" style="background:#7656d6;color:#fff" onclick="customerPaymentLink(' + chr(39) + chr(36) + '{c.id}' + chr(39) + ')">🔗 Payment Link</button>'
    s=s.replace("Details</button>","Details</button>"+add,1)

marker="function startup(){"
if "function sendOneSms(phone,name)" not in s:
    block=r'''function sendOneSms(phone,name){window.__starSmsPhone=String(phone||'');openSheet('<h3>📩 Send SMS</h3><div class="muted">To: '+esc(name||'Customer')+' • '+esc(phone)+'</div><textarea id="onesms" class="input" rows="6" placeholder="Write your own message"></textarea><button class="btn dark full" onclick="doSendOneSms()">✉️ Send SMS</button>')}
function doSendOneSms(){let msg=document.getElementById('onesms')?.value||'',phone=window.__starSmsPhone||'';if(!msg.trim()){toast('Write a message first');return}if(!window.AndroidBridge||typeof AndroidBridge.sendSms!=='function'){toast('SMS service unavailable');return}try{let ok=AndroidBridge.sendSms(phone,msg);if(ok){closeSheet();toast('SMS sent from SIM')}}catch(e){toast('SMS failed: '+(e.message||'unknown error'))}}
function customerPaymentLink(id){let c=d.customers.find(x=>String(x.id)===String(id));if(!c){toast('Customer not found');return}let base='https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html';let q=new URLSearchParams({code:String(c.id||''),name:String(c.name||''),location:String(c.address||''),package:String(c.pkg||''),bill:String(c.fee||0),prev:String(c.prevDue||0),total:String(due(c)),merchant:String(d.settings.merchantNumber||'01897-099850')});let link=base+'?'+q.toString();window.__starPay={link:link,phone:String(c.phone||''),name:String(c.name||'Customer')};openSheet('<h3>🔗 Payment Link</h3><div class="muted">'+esc(c.id)+' • '+esc(c.name)+'</div><textarea id="paylink" class="input" rows="4" readonly>'+esc(link)+'</textarea><button class="btn full" onclick="copyCustomerPaymentLink()">📋 Copy Link</button><button class="btn dark full" style="margin-top:7px" onclick="sendPaymentLinkSms()">✉️ Send SMS</button><button class="btn light full" style="margin-top:7px" onclick="openPaymentPage()">🌐 Open Payment Page</button>')}
async function copyCustomerPaymentLink(){let x=window.__starPay?.link||'';if(!x){toast('Payment link not found');return}try{if(window.AndroidBridge&&typeof AndroidBridge.copyText==='function'){if(AndroidBridge.copyText(x)){toast('Payment link copied');return}}if(navigator.clipboard&&navigator.clipboard.writeText){await navigator.clipboard.writeText(x);toast('Payment link copied');return}let t=document.getElementById('paylink');t.focus();t.select();t.setSelectionRange(0,t.value.length);toast(document.execCommand('copy')?'Payment link copied':'Select and copy the link manually')}catch(e){toast('Copy failed — long press the link to copy')}}
function openPaymentPage(){let x=window.__starPay?.link||'';if(!x)return;if(window.AndroidBridge&&typeof AndroidBridge.openExternalUrl==='function'){AndroidBridge.openExternalUrl(x)}else{location.href=x}}
function sendPaymentLinkSms(){let x=window.__starPay;if(!x){toast('Payment link not found');return}let msg='Your bill payment link: '+x.link;if(!window.AndroidBridge||typeof AndroidBridge.sendSms!=='function'){toast('SMS service unavailable');return}try{let ok=AndroidBridge.sendSms(x.phone,msg);if(ok){closeSheet();toast('Payment link SMS sent from SIM')}}catch(e){toast('SMS failed: '+(e.message||'unknown error'))}}
'''
    if marker not in s:
        raise SystemExit("startup marker not found")
    s=s.replace(marker,block+marker,1)
HTML.write_text(s,encoding="utf-8")

JAVA=Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
j=JAVA.read_text(encoding="utf-8")
if "private String pendingSmsPhone" not in j:
    j=j.replace("private static final int SMS_PERMISSION_REQUEST = 7001;","private static final int SMS_PERMISSION_REQUEST = 7001;\n    private String pendingSmsPhone = \"\";\n    private String pendingSmsMessage = \"\";",1)
new='''@JavascriptInterface public boolean sendSms(String phone,String message){
            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty())return false;
            String p=phone.trim(), m=message.trim();
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                pendingSmsPhone=p; pendingSmsMessage=m;
                runOnUiThread(()->{Toast.makeText(MainActivity.this,"Allow SMS permission. After permission, the SMS will be sent from SIM.",Toast.LENGTH_LONG).show();requestSmsPermission();});
                return false;
            }
            return sendSmsNow(p,m);
        }
        private boolean sendSmsNow(String p,String m){
            try{
                SmsManager sms=SmsManager.getDefault();
                java.util.ArrayList<String> parts=sms.divideMessage(m);
                if(parts.size()>1) sms.sendMultipartTextMessage(p,null,parts,null,null);
                else sms.sendTextMessage(p,null,m,null,null);
                runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS sent from SIM balance",Toast.LENGTH_SHORT).show());
                return true;
            }catch(Exception e){
                runOnUiThread(()->Toast.makeText(MainActivity.this,"SIM SMS failed: "+e.getMessage(),Toast.LENGTH_LONG).show());
                return false;
            }
        }'''
pat=re.compile(r'@JavascriptInterface public boolean sendSms\(String phone,String message\)\{.*?\n        \}\n        @JavascriptInterface public void sendBulk',re.S)
m=pat.search(j)
if not m: raise SystemExit("sendSms method not found")
j=j[:m.start()]+new+'\n        @JavascriptInterface public void sendBulk'+j[m.end():]
old='''if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "SIM SMS permission enabled", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "SMS permission denied. Direct SIM SMS cannot work.", Toast.LENGTH_LONG).show();
            }'''
rep='''if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "SIM SMS permission enabled", Toast.LENGTH_SHORT).show();
                if(!pendingSmsPhone.isEmpty() && !pendingSmsMessage.isEmpty()){
                    String p=pendingSmsPhone, m=pendingSmsMessage;
                    pendingSmsPhone=""; pendingSmsMessage="";
                    boolean ok=sendSmsNow(p,m);
                    if(ok && webView!=null) webView.evaluateJavascript("try{closeSheet();toast('SMS sent from SIM')}catch(e){}",null);
                }
            } else {
                Toast.makeText(this, "SMS permission denied. Allow SMS permission and press Send SMS again.", Toast.LENGTH_LONG).show();
            }'''
if old not in j: raise SystemExit("permission callback block not found")
j=j.replace(old,rep,1)
JAVA.write_text(j,encoding="utf-8")
print("66.91 SMS + payment-link SMS patch ready")
