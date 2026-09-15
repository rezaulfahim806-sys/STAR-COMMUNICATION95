from pathlib import Path

html=Path('app/src/main/assets/index.html')
s=html.read_text(encoding='utf-8')
script=r'''<script>
(function(){
 if(window.__starSmsCustomerListFix)return; window.__starSmsCustomerListFix=true;
 function list(){return (window.d&&Array.isArray(d.customers))?d.customers:[];}
 function phone(c){return String(c.phone||c.mobile||c.mobileNumber||c.contact||c.msisdn||'').trim();}
 function total(c){return typeof due==='function'?Number(due(c)||0):Number(c.prevDue||c.previousDue||0)+Number(c.fee||c.monthlyFee||0);}
 function filter(a,f){return a.filter(function(c){var st=String(c.status||'').toLowerCase();if(f==='active')return st==='active';if(f==='inactive')return st==='inactive';if(f==='expired')return st==='expired';if(f==='paid')return typeof paid==='function'&&Number(paid(c))>0;if(f==='unpaid')return total(c)>0;return true;});}
 window.starSmsCustomerList=function(kind){
   var f=kind||'all',a=filter(list(),f),n=a.filter(function(c){return phone(c);});
   if(!n.length){toast('এই তালিকায় mobile number নেই');return;}
   var rows=n.map(function(c){var id=String(c.id);return '<label style="display:flex;gap:9px;align-items:center;padding:10px 4px;border-bottom:1px solid #eef1f5"><input class="starSmsPick" type="checkbox" value="'+esc(id)+'" checked><span style="flex:1"><b>'+esc(c.name||'Customer')+'</b><br><span class="muted">'+esc(c.clientCode||id)+' • '+esc(phone(c))+' • '+esc(c.status||'')+'</span></span></label>';}).join('');
   var title={all:'All Customers',active:'Active Customers',inactive:'Inactive Customers',expired:'Expired Customers',paid:'Paid Customers',unpaid:'Unpaid Customers'}[f]||'Customers';
   openSheet('<h3>📩 Send SMS — '+title+'</h3><div class="row" style="margin-bottom:7px"><button class="btn light" onclick="starSmsCustomerList(\'all\')">All</button><button class="btn light" onclick="starSmsCustomerList(\'active\')">Active</button><button class="btn light" onclick="starSmsCustomerList(\'inactive\')">Inactive</button></div><div style="max-height:250px;overflow:auto;border:1px solid #e3e8ef;border-radius:10px;padding:3px">'+rows+'</div><textarea id="starSmsListMsg" class="input" rows="5" placeholder="Write SMS message"></textarea><button class="btn dark full" onclick="starSendSelectedSms()">📨 Send to Selected</button>');
 };
 window.starSendSelectedSms=function(){
   var ids=[].slice.call(document.querySelectorAll('.starSmsPick:checked')).map(function(x){return String(x.value);});
   var msg=(document.getElementById('starSmsListMsg')||{}).value||'';msg=msg.trim();
   if(!ids.length){toast('Select at least one customer');return;} if(!msg){toast('Write a message first');return;}
   var a=list().filter(function(c){return ids.indexOf(String(c.id))>=0&&phone(c);});closeSheet();
   a.forEach(function(c,i){setTimeout(function(){var m=msg.replace(/\{name\}/g,String(c.name||'Customer')).replace(/\{code\}/g,String(c.clientCode||c.id||'')).replace(/\{total\}/g,'৳'+Number(total(c)).toLocaleString('en-US'));if(window.AndroidBridge&&AndroidBridge.sendSms){try{AndroidBridge.sendSms(phone(c),m);return;}catch(e){}}try{location.href='smsto:'+encodeURIComponent(phone(c))+'?body='+encodeURIComponent(m);}catch(e){}},i*700);});
   toast('SMS started: '+a.length);
 };
 function add(){if(typeof page==='undefined'||page!=='customers')return;var content=document.getElementById('content');if(!content||document.getElementById('starSeparateSmsButton'))return;var b=document.createElement('button');b.id='starSeparateSmsButton';b.className='btn dark full';b.style.margin='0 0 8px';b.textContent='📩 Send SMS — Customer List';b.onclick=function(){starSmsCustomerList('all');};content.insertBefore(b,content.firstChild);}
 setInterval(add,500);
})();
</script>
'''
s=s.replace('</body>',script+'</body>',1)
html.write_text(s,encoding='utf-8')
print('Separate SMS customer selection list added')
