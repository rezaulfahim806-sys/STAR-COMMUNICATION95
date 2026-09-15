from pathlib import Path

html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

script = r'''<script>
(function(){
  if(window.__starLineOffSmsFix)return;
  window.__starLineOffSmsFix=true;
  function customers(){return (window.d&&Array.isArray(d.customers))?d.customers:[];}
  function phone(c){return String(c.phone||c.mobile||c.mobileNumber||c.contact||'').trim();}
  function offCustomers(){return customers().filter(function(c){var st=String(c.status||'').toLowerCase();return st==='inactive'||st==='expired';}).filter(function(c){return phone(c);});}
  function openSms(c,msg){try{if(window.AndroidBridge&&AndroidBridge.openSmsComposer){AndroidBridge.openSmsComposer(phone(c),msg);return true;}location.href='smsto:'+encodeURIComponent(phone(c))+'?body='+encodeURIComponent(msg);return true;}catch(e){return false;}}
  window.starLineOffSms=function(){
    var a=offCustomers();
    if(!a.length){toast('Inactive/Expired customer with mobile number নেই');return;}
    openSheet('<h3>📴 Line Off SMS</h3><div class="muted">Inactive/Expired customers: '+a.length+'</div><textarea id="starLineOffMsg" class="input" rows="7">STAR COMMUNICATION\nDear {name},\nYour internet line is currently disconnected/inactive. Please contact us or clear your due bill to restore the connection.\nClient Code: {code}\nTotal Due: {total}</textarea><button class="btn dark full" onclick="starSendLineOffSms()">📨 Send Line Off SMS</button>');
  };
  window.starSendLineOffSms=function(){
    var e=document.getElementById('starLineOffMsg'),tpl=e?e.value.trim():'';
    if(!tpl){toast('Write a message first');return;}
    var a=offCustomers();closeSheet();
    a.forEach(function(c,i){setTimeout(function(){var total=typeof due==='function'?due(c):Number(c.prevDue||c.previousDue||0)+Number(c.fee||c.monthlyFee||0);var msg=tpl.replace(/\{name\}/g,String(c.name||'Customer')).replace(/\{code\}/g,String(c.clientCode||c.id||'')).replace(/\{total\}/g,'৳'+Number(total).toLocaleString('en-US'));openSms(c,msg);},i*800);});
    toast('Line Off SMS started: '+a.length);
  };
  function add(){
    if(typeof page==='undefined'||page!=='customers')return;
    var content=document.getElementById('content');
    if(!content||document.getElementById('starLineOffSmsBtn'))return;
    var btn=document.createElement('button');btn.id='starLineOffSmsBtn';btn.className='btn red full';btn.style.margin='0 0 8px';btn.textContent='📴 Send Line Off SMS';btn.onclick=starLineOffSms;
    var toolbar=document.getElementById('starCustomerToolbar');
    if(toolbar)toolbar.parentNode.insertBefore(btn,toolbar.nextSibling);else content.insertBefore(btn,content.firstChild);
  }
  setInterval(add,700);
})();
</script>
'''

if 'starLineOffSmsFix' not in s:
    s = s.replace('</body>', script + '</body>', 1)
    html.write_text(s, encoding='utf-8')
print('Line Off SMS option added')
