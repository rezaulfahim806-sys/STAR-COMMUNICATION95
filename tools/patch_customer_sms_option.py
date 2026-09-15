from pathlib import Path

p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
D=chr(36)
cid=D+"{c.id}"
escp=D+"{esc(c.phone)}"
old1='<button class="small view" onclick="go(\\'details\\',{id:\\''+cid+'\\'})">Details</button>'
if "function smsCustomer(id)" not in s:
    if old1 not in s: raise SystemExit("Customer Details button not found")
    s=s.replace(old1, old1+'<button class="small view" onclick="smsCustomer(\\''+cid+'\\')">📩 SMS</button>',1)
old2='<button class="small wa" onclick="waCustomer(\\''+escp+'\\')">WhatsApp</button>'
if "function smsCustomer(id)" not in s:
    if old2 not in s: raise SystemExit("Details WhatsApp button not found")
    s=s.replace(old2, old2+'<button class="small view" onclick="smsCustomer(\\''+cid+'\\')">📩 SMS</button>',1)
if "function smsCustomer(id)" not in s:
    anchor="function callCustomer(n){"
    if anchor not in s: raise SystemExit("callCustomer anchor not found")
    fn=r'''function smsCustomer(id){let c=d.customers.find(x=>String(x.id)===String(id));if(!c){toast('Customer not found');return}openSheet('<h3>📩 Send SMS</h3><div class=muted>To: '+esc(c.phone||'')+' • '+esc(c.name||'Customer')+'</div><textarea id="smsmsg" class="input" rows="6" placeholder="Write message"></textarea><button class="btn dark full" onclick="sendCustomerSms(\''+c.id+'\')">📨 Send SMS</button>');}function sendCustomerSms(id){let c=d.customers.find(x=>String(x.id)===String(id));if(!c){toast('Customer not found');return}let el=document.getElementById('smsmsg'),m=el?el.value.trim():'';if(!m){toast('Write a message first');return}if(window.AndroidBridge&&AndroidBridge.sendSms){AndroidBridge.sendSms(String(c.phone||''),m);closeSheet()}else{location.href='sms:'+String(c.phone||'')+'?body='+encodeURIComponent(m);}}'''
    s=s.replace(anchor,fn+anchor,1)

# Add an All Customer Payment Link SMS button to Billing. Each message is personalized
# with customer name, client code, total due and that customer's own payment URL.
if 'function starAllPaymentLinkSms' not in s:
    script=r'''<script>
(function(){
  function paymentLink(c){
    var q=new URLSearchParams();
    q.set('code',String(c.clientCode||c.id||''));
    q.set('name',String(c.name||'Customer'));
    q.set('location',String(c.address||c.location||''));
    q.set('package',String(c.pkg||c.packageName||''));
    q.set('bill',String(Number(c.fee||c.monthlyFee||0)));
    q.set('prev',String(Number(c.prevDue||c.previousDue||0)));
    q.set('total',String(typeof due==='function'?due(c):Number(c.prevDue||c.previousDue||0)+Number(c.fee||c.monthlyFee||0)));
    q.set('merchant',String((d.settings&&d.settings.merchantNumber)||'01897-099850'));
    return 'https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html?'+q.toString();
  }
  window.starAllPaymentLinkSms=function(){
    var list=(window.d&&Array.isArray(d.customers))?d.customers.filter(function(c){return c&&c.phone;}):[];
    if(!list.length){toast('No customer mobile numbers found');return;}
    openSheet('<h3>📩 All Customer Payment SMS</h3><div class="muted">প্রত্যেক Customer-এর নিজের নাম, Client Code, Total Due এবং আলাদা Payment Link যাবে।</div><textarea id="allPaySms" class="input" rows="7">STAR COMMUNICATION\nপ্রিয় {name}, আপনার বর্তমান মোট বকেয়া {due}। নিচের Payment Link-এ গিয়ে বিল পরিশোধ করুন:\n{link}\nধন্যবাদ।</textarea><button class="btn dark full" onclick="sendAllPaymentLinkSms()">📨 Send Payment Link to All</button><button class="btn light full" style="margin-top:7px" onclick="closeSheet()">Cancel</button>');
  };
  window.sendAllPaymentLinkSms=function(){
    var el=document.getElementById('allPaySms'),tpl=el?el.value.trim():'';
    if(!tpl){toast('Write a message first');return}
    var list=(window.d&&Array.isArray(d.customers))?d.customers.filter(function(c){return c&&c.phone;}):[];
    if(!list.length){toast('No customer mobile numbers found');return}
    closeSheet();
    var i=0;
    function next(){
      if(i>=list.length){toast('All customer SMS process finished');return}
      var c=list[i++],total=typeof due==='function'?due(c):Number(c.prevDue||c.previousDue||0)+Number(c.fee||c.monthlyFee||0);
      var msg=tpl.replace(/\{name\}/g,String(c.name||'Customer')).replace(/\{due\}/g,money(total)).replace(/\{link\}/g,paymentLink(c));
      try{if(window.AndroidBridge&&AndroidBridge.sendSms)AndroidBridge.sendSms(String(c.phone).trim(),msg);else location.href='smsto:'+encodeURIComponent(String(c.phone).trim())+'?body='+encodeURIComponent(msg);}catch(e){}
      setTimeout(next,500);
    }
    next();
  };
  function addAllPaymentSmsButton(){
    if(document.getElementById('allPaymentLinkSmsBtn'))return;
    var sections=document.querySelectorAll('.section');
    for(var i=0;i<sections.length;i++){
      var h=sections[i].querySelector('h3');
      if(h&&/This Month/i.test(h.textContent||'')){
        var b=document.createElement('button');b.id='allPaymentLinkSmsBtn';b.className='btn dark full';b.style.marginTop='7px';b.textContent='📩 All Customer Payment Link SMS';b.onclick=starAllPaymentLinkSms;sections[i].appendChild(b);return;
      }
    }
  }
  var oldRender=window.render;
  if(oldRender&&!window.__allPaymentSmsRender){window.__allPaymentSmsRender=true;window.render=function(){oldRender();setTimeout(addAllPaymentSmsButton,80);};}
  setTimeout(addAllPaymentSmsButton,250);
})();
</script>
'''
    s=s.replace('</body>',script+'</body>',1)

p.write_text(s,encoding="utf-8")
print("Per-customer SMS and All Customer Payment Link SMS options ready")
