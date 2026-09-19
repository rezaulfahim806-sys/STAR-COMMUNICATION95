from pathlib import Path
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
old="""function doSendOneSms(){let msg=document.getElementById('onesms')?.value||'',phone=window.__starSmsPhone||'';if(!msg.trim()){toast('Write a message first');return}if(!window.AndroidBridge||typeof AndroidBridge.sendSms!=='function'){toast('SMS service unavailable');return}try{let ok=AndroidBridge.sendSms(phone,msg);if(ok){closeSheet();toast('SMS sent')}}catch(e){toast('SMS failed: '+(e.message||'unknown error'))}}"""
new="""function doSendOneSms(){let el=document.getElementById('onesms'),msg=el?String(el.value||'').trim():'',phone=String(window.__starSmsPhone||'').trim();if(!phone){toast('Customer phone number missing');return}if(!msg){toast('Write a message first');if(el)el.focus();return}try{if(window.AndroidBridge&&typeof AndroidBridge.sendSms==='function'){let ok=AndroidBridge.sendSms(phone,msg);if(ok){closeSheet();return}}}catch(e){}try{window.location.href='smsto:'+encodeURIComponent(phone)+'?body='+encodeURIComponent(msg)}catch(e){toast('SMS app could not be opened')}}"""
if old not in s:
    raise SystemExit("SMS function not found after account patch")
p.write_text(s.replace(old,new,1),encoding="utf-8")
print("Customer-box SMS only patch applied")
