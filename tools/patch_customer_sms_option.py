from pathlib import Path

html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

script = r'''<script>
(function(){
  function list(){ return (typeof d!=='undefined' && Array.isArray(d.customers)) ? d.customers : []; }
  function phone(c){ return String((c&&(c.phone||c.mobile||c.mobileNumber||c.contact||c.msisdn))||'').trim(); }
  function find(id){ var x=String(id==null?'':id); return list().find(function(c){return String(c.id)===x||String(c.clientCode||'')===x;}); }
  function total(c){ return typeof due==='function' ? Number(due(c)||0) : Number(c.prevDue||c.previousDue||0)+Number(c.fee||c.monthlyFee||0); }
  function sms(c,msg){ var p=phone(c); if(!p){toast('Customer mobile number নেই');return false;} try{ if(window.AndroidBridge&&typeof AndroidBridge.sendSms==='function'){ var ok=AndroidBridge.sendSms(p,msg); return ok===true; } }catch(e){} try{location.href='smsto:'+encodeURIComponent(p)+'?body='+encodeURIComponent(msg);return true}catch(e){toast('SMS app could not be opened');return false;} }
  window.starCustomerSms=function(id){var c=find(id);if(!c){toast('Customer not found');return;}openSheet('<h3>📩 Send SMS</h3><div class="muted">To: '+esc(c.name||'Customer')+' • '+esc(phone(c)||'No mobile')+'</div><textarea id="starOneMsg" class="input" rows="6" placeholder="Write your own message"></textarea><button class="btn dark full" onclick="starSendOne('+JSON.stringify(String(c.id))+')">📨 Send SMS</button>');};
  window.starSendOne=function(id){var c=find(id),e=document.getElementById('starOneMsg'),m=e?e.value.trim():'';if(!c)return;if(!m){toast('Write a message first');return;}if(sms(c,m)){closeSheet();}else{toast('SMS permission allow kore abar Send SMS chapun');}};
  function filtered(){var f=(typeof opts!=='undefined'&&opts.filter)||'all';return list().filter(function(c){if(f==='expired')return String(c.status||'').toLowerCase()==='expired';if(f==='paid')return typeof paid==='function'&&Number(paid(c))>0;if(f==='unpaid')return total(c)>0;if(f==='active')return String(c.status||'').toLowerCase()==='active';if(f==='inactive')return String(c.status||'').toLowerCase()==='inactive';return true;});}
  window.starFilterSms=function(){var a=filtered().filter(function(c){return phone(c);});if(!a.length){toast('এই তালিকায় mobile number নেই');return;}var f=(typeof opts!=='undefined'&&opts.filter)||'all',n={all:'All Customers',paid:'Paid Customers',unpaid:'Unpaid Customers',expired:'Expired Customers',active:'Active Customers',inactive:'Inactive Customers'}[f]||'Customers';openSheet('<h3>📩 Send Message — '+n+'</h3><div class="muted">Recipients: '+a.length+'</div><textarea id="starBulkMsg" class="input" rows="6" placeholder="Write your own message"></textarea><button class="btn dark full" onclick="starSendFiltered()">📨 Send to '+n+'</button>');};
  window.starSendFiltered=function(){var e=document.getElementById('starBulkMsg'),m=e?e.value.trim():'';if(!m){toast('Write a message first');return;}var a=filtered().filter(function(c){return phone(c);});closeSheet();a.forEach(function(c,i){setTimeout(function(){sms(c,m);},i*650);});toast('SMS started: '+a.length);};
  function link(c){var q=new URLSearchParams();q.set('code',String(c.clientCode||c.id||''));q.set('name',String(c.name||'Customer'));q.set('location',String(c.address||c.location||''));q.set('package',String(c.pkg||c.packageName||''));q.set('bill',String(Number(c.fee||c.monthlyFee||0)));q.set('prev',String(Number(c.prevDue||c.previousDue||0)));q.set('total',String(total(c)));q.set('merchant',String((d.settings&&d.settings.merchantNumber)||'01897-099850'));return 'https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html?'+q.toString();}
  window.starAllPaymentLinkSms=function(){var a=list().filter(function(c){return phone(c);});if(!a.length){toast('No customer mobile numbers found');return;}openSheet('<h3>🔗 Send Payment Link SMS</h3><div class="muted">Each customer gets their own Payment Link. Existing Payment → Send SMS remains unchanged.</div><textarea id="starPayMsg" class="input" rows="7">STAR COMMUNICATION\nDear {name},\nClient Code: {code}\nTotal Due: {total}\nPayment Link: {link}</textarea><button class="btn green full" onclick="starSendLinks()">📨 Send Payment Link SMS</button>');};
  window.starSendLinks=function(){var e=document.getElementById('starPayMsg'),tpl=e?e.value.trim():'';if(!tpl){toast('Write a message first');return;}var a=list().filter(function(c){return phone(c);});closeSheet();a.forEach(function(c,i){setTimeout(function(){var m=tpl.replace(/\{name\}/g,String(c.name||'Customer')).replace(/\{code\}/g,String(c.clientCode||c.id||'')).replace(/\{total\}/g,'৳'+Number(total(c)).toLocaleString('en-US')).replace(/\{link\}/g,link(c));sms(c,m);},i*650);});toast('Payment Link SMS started: '+a.length);};
  function rows(kind){return list().filter(function(c){if(kind==='paid')return typeof paid==='function'&&Number(paid(c))>0;if(kind==='unpaid')return total(c)>0;if(kind==='expired')return String(c.status||'').toLowerCase()==='expired';return true;});}
  window.exportCustomerPDF=function(kind){var a=rows(kind),name=kind==='paid'?'Paid Customer List':kind==='unpaid'?'Unpaid Customer List':kind==='expired'?'Expired Customer List':'All Customer List';if(!a.length){toast('No customers in this list');return;}var rowsData=a.map(function(c,i){return{serial:i+1,id:String(c.clientCode||c.id||''),name:String(c.name||'Customer'),phone:phone(c),address:String(c.address||c.location||''),pkg:String(c.pkg||c.packageName||''),fee:Number(c.fee||c.monthlyFee||0),pppoe:String(c.pppoe||c.pppoeUser||c.pppoeUsername||''),pppoePassword:String(c.pppoePassword||c.pppoePass||c.password||''),onu:String(c.onu||c.onuId||''),connectionDate:String(c.connectionDate||c.createdAt||'—'),expiry:String(c.expiry||c.expiryDate||'—'),prevDue:Number(c.prevDue||c.previousDue||0),runningBill:Number((typeof billDue==='function'?billDue(c):0)||0),totalDue:Number(total(c)||0),status:String(c.status||'').toUpperCase()};});if(window.AndroidBridge&&typeof AndroidBridge.createCustomerPdf==='function'){AndroidBridge.createCustomerPdf(JSON.stringify({title:name,rows:rowsData}));return;}window.print();};  window.exportCustomersPDF=function(){exportCustomerPDF('all');};
  window.exportCustomersCSV=function(){var a=list(),rows=[['Client Code','Name','Mobile','Address','Package','Monthly Fee','Previous Due','Total Due','Status','Connection Date','Expiry Date']];a.forEach(function(c){rows.push([c.clientCode||c.id||'',c.name||'',phone(c),c.address||c.location||'',c.pkg||c.packageName||'',c.fee||c.monthlyFee||0,c.prevDue||c.previousDue||0,total(c),c.status||'',c.createdAt||c.connectionDate||'',c.expiry||c.expiryDate||'']);});var csv=rows.map(function(r){return r.map(function(v){return '"'+String(v==null?'':v).replace(/"/g,'""')+'"';}).join(',');}).join('\n');if(window.AndroidBridge&&AndroidBridge.saveTextFile){AndroidBridge.saveTextFile('STAR_COMMUNICATION_Customers.csv',csv,'text/csv');toast('CSV saved in Downloads');}else{var blob=new Blob([csv],{type:'text/csv'}),u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download='STAR_COMMUNICATION_Customers.csv';a.click();setTimeout(function(){URL.revokeObjectURL(u)},1000);}};
  window.starCustomerTools=function(){openSheet('<h3>👥 Customer Tools</h3><button class="btn dark full" onclick="starFilterSms()">💬 Send Message</button><button class="btn green full" style="margin-top:7px" onclick="starAllPaymentLinkSms()">🔗 Send Payment Link SMS</button><button class="btn light full" style="margin-top:7px" onclick="exportCustomersCSV()">📊 Download Customer CSV</button><button class="btn light full" style="margin-top:7px" onclick="exportCustomerPDF(\'all\')">📄 Download All Customer List PDF</button>');};
  function addSms(card,c){if(!card||!c||card.querySelector('[data-star-customer-sms]'))return;var a=card.querySelector('.actions');if(!a)return;var b=document.createElement('button');b.className='small view';b.textContent='📩 SMS';b.setAttribute('data-star-customer-sms','1');b.onclick=function(){starCustomerSms(c.id);};a.appendChild(b);}
  function enhance(){if(typeof page==='undefined')return;if(page==='customers'){var content=document.getElementById('content');if(content&&!document.getElementById('starCustomerToolbar')){var b=document.createElement('div');b.className='section';b.id='starCustomerToolbar';b.innerHTML='<h3>👥 Customer Tools</h3><div class="row"><button class="btn dark" onclick="starFilterSms()">📩 Send SMS</button><button class="btn light" onclick="starCustomerTools()">⚙️ More</button></div>';content.insertBefore(b,content.firstChild);}document.querySelectorAll('.customer').forEach(function(card){var m=card.textContent.match(/SC\d+/),c=m?list().find(function(x){return String(x.clientCode||'')===m[0];}):null;if(c)addSms(card,c);});var p=document.querySelectorAll('.pdfbtn');if(p.length>=4){p[0].textContent='📄 All Customer List PDF';p[1].textContent='📄 Unpaid Customer List PDF';p[2].textContent='📄 Expired Customer List PDF';p[3].textContent='📄 Paid Customer List PDF';}}if(page==='details'){var c=find(typeof opts!=='undefined'&&opts.id),a=document.querySelector('.actions');if(c&&a){addSms({querySelector:function(){return a;}},c);}}}
  var oldGo=window.go;if(oldGo&&!window.__starSmsPdfGo){window.__starSmsPdfGo=true;window.go=function(p,o,push){oldGo(p,o,push);setTimeout(enhance,150);};}
  setInterval(enhance,700);
})();
</script>
'''
if 'starSmsPdfFixV3' not in s:
    script = script.replace('<script>', '<script>window.starSmsPdfFixV3=true;', 1)
    s = s.replace('</body>', script + '</body>', 1)
import re
# ONLY fix the individual Customer-card SMS button. Do not change Payment Link SMS.
pat = re.compile(r'function doSendOneSms\(\)\{.*?\}', re.S)
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
  toast('SMS app could not be opened');
}'''
if pat.search(s):
    s=pat.sub(new_fn,s,count=1)
html.write_text(s, encoding='utf-8')
print('Customer-card SMS fixed only; payment-link SMS untouched')