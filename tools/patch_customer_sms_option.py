from pathlib import Path
import re

html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

# ONLY fix the individual Customer-card SMS handler.
# Do not add any extra script and do not modify Payment Link SMS.
pat = re.compile(r'function doSendOneSms\(\)\{[\s\S]*?(?=\nfunction customerPaymentLink)', re.S)
new_fn = r'''function doSendOneSms(){
  let el=document.getElementById('onesms');
  let msg=el?String(el.value||'').trim():'';
  let phone=String(window.__starSmsPhone||'').trim();
  if(!phone){toast('Customer phone number missing');return}
  if(!msg){toast('Write a message first');if(el)el.focus();return}
  try{
    if(window.AndroidBridge&&typeof AndroidBridge.openSmsComposer==='function'){
      if(AndroidBridge.openSmsComposer(phone,msg)){closeSheet();return}
    }
  }catch(e){}
  try{
    window.location.href='smsto:'+encodeURIComponent(phone)+'?body='+encodeURIComponent(msg);
  }catch(e){
    toast('SMS app could not be opened');
  }
}'''
if not pat.search(s):
    raise SystemExit('doSendOneSms boundary not found')
s = pat.sub(new_fn, s, count=1)
html.write_text(s, encoding='utf-8')
print('Customer-card SMS handler fixed only; Payment Link SMS untouched')
