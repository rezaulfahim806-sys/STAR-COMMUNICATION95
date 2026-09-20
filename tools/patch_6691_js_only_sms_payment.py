from pathlib import Path
html=Path("app/src/main/assets/index.html")
s=html.read_text(encoding="utf-8")

if "function customerPaymentLink(id)" not in s:
    marker="function startup(){"
    block="""function sendOneSms(phone,name){window.__starSmsPhone=String(phone||'');openSheet('<h3>📩 Send SMS</h3><div class="muted">To: '+esc(name||'Customer')+' • '+esc(phone)+'</div><textarea id="onesms" class="input" rows="6" placeholder="Write your own message"></textarea><button class="btn dark full" onclick="doSendOneSms()">✉️ Send SMS</button>')}
function doSendOneSms(){var msg=(document.getElementById('onesms')||{}).value||'',phone=window.__starSmsPhone||'';if(!msg.trim()){toast('Write a message first');return}if(!window.AndroidBridge||typeof AndroidBridge.sendSms!=='function'){toast('SMS service unavailable');return}try{if(AndroidBridge.sendSms(phone,msg)){closeSheet();toast('SMS sent from SIM')}}catch(e){toast('SMS failed')}}
function customerPaymentLink(id){var c=(d.customers||[]).find(function(x){return String(x.id)===String(id)});if(!c){toast('Customer not found');return}var link='https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html?code='+encodeURIComponent(c.id||'')+'&name='+encodeURIComponent(c.name||'')+'&location='+encodeURIComponent(c.address||'')+'&package='+encodeURIComponent(c.pkg||'')+'&bill='+encodeURIComponent(c.fee||0)+'&prev='+encodeURIComponent(c.prevDue||0)+'&total='+encodeURIComponent(due(c));window.__starPay={link:link,phone:String(c.phone||''),name:String(c.name||'Customer')};openSheet('<h3>🔗 Payment Link</h3><textarea id="paylink" class="input" rows="4" readonly>'+esc(link)+'</textarea><button class="btn full" onclick="copyCustomerPaymentLink()">📋 Copy Link</button><button class="btn dark full" style="margin-top:7px" onclick="sendPaymentLinkSms()">✉️ Send SMS</button><button class="btn light full" style="margin-top:7px" onclick="openPaymentPage()">🌐 Open Payment Page</button>')}
function copyCustomerPaymentLink(){var x=window.__starPay&&window.__starPay.link;if(!x)return;try{if(window.AndroidBridge&&AndroidBridge.copyText&&AndroidBridge.copyText(x)){toast('Payment link copied');return}var t=document.getElementById('paylink');t.focus();t.select();document.execCommand('copy');toast('Payment link copied')}catch(e){toast('Copy failed')}}
function openPaymentPage(){var x=window.__starPay&&window.__starPay.link;if(!x)return;if(window.AndroidBridge&&AndroidBridge.openExternalUrl)AndroidBridge.openExternalUrl(x);else location.href=x}
function sendPaymentLinkSms(){var x=window.__starPay;if(!x)return;var msg='Your bill payment link: '+x.link;try{if(window.AndroidBridge&&AndroidBridge.sendSms&&AndroidBridge.sendSms(x.phone,msg)){closeSheet();toast('Payment link SMS sent from SIM')}}catch(e){toast('SMS failed')}}
"""
    if marker not in s: raise SystemExit("startup marker not found")
    s=s.replace(marker,block+marker,1)

if "onclick="+""sendOneSms(c.phone" not in s:
    if "Details</button>" not in s: raise SystemExit("customer Details button not found")
    add='<button class="small view" onclick="sendOneSms(c.phone,c.name)">📩 SMS</button><button class="small" style="background:#7656d6;color:#fff" onclick="customerPaymentLink(c.id)">🔗 Payment Link</button>'
    s=s.replace("Details</button>","Details</button>"+add,1)

html.write_text(s,encoding="utf-8")
print("66.91 JS-only SMS/payment fix applied")
