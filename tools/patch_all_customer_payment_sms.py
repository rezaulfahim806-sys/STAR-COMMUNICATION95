from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

# Runs after MainActivity's injected message-center code and replaces only the bulk
# message behavior. Existing per-customer SMS and Payment Link actions remain intact.
if 'function starAllPaymentLinkSms' not in s:
    script=r'''<script>
(function(){
  function linkForAll(c){
    var q=new URLSearchParams();
    var code=String(c.clientCode||c.id||'');
    q.set('code',code);q.set('name',String(c.name||'Customer'));
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
    var tpl=(document.getElementById('allPaySms')||{}).value||'';
    tpl=tpl.trim();
    if(!tpl){toast('Write a message first');return;}
    var list=(window.d&&Array.isArray(d.customers))?d.customers.filter(function(c){return c&&c.phone;}):[];
    if(!list.length){toast('No customer mobile numbers found');return;}
    closeSheet();
    var i=0;
    function next(){
      if(i>=list.length){toast('All customer SMS process finished');return;}
      var c=list[i++],total=typeof due==='function'?due(c):Number(c.prevDue||c.previousDue||0)+Number(c.fee||c.monthlyFee||0);
      var msg=tpl.replace(/\{name\}/g,String(c.name||'Customer')).replace(/\{due\}/g,money(total)).replace(/\{link\}/g,linkForAll(c));
      try{if(window.AndroidBridge&&AndroidBridge.sendSms)AndroidBridge.sendSms(String(c.phone).trim(),msg);else location.href='smsto:'+encodeURIComponent(String(c.phone).trim())+'?body='+encodeURIComponent(msg);}catch(e){}
      setTimeout(next,450);
    }
    next();
  };
  function addButton(){
    if(document.getElementById('allPaymentLinkSmsBtn'))return;
    var sections=document.querySelectorAll('.section');
    for(var i=0;i<sections.length;i++){
      var h=sections[i].querySelector('h3');
      if(h&&/This Month|Customer Bill Payment/i.test(h.textContent||'')){
        var b=document.createElement('button');b.id='allPaymentLinkSmsBtn';b.className='btn dark full';b.style.marginTop='7px';b.textContent='📩 All Customer Payment Link SMS';b.onclick=starAllPaymentLinkSms;sections[i].appendChild(b);return;
      }
    }
  }
  setTimeout(addButton,250);
  var oldRender=window.render;
  if(oldRender&&!window.__allPaymentSmsRender){window.__allPaymentSmsRender=true;window.render=function(){oldRender();setTimeout(addButton,80);};}
})();
</script>
'''
    s=s.replace('</body>',script+'</body>',1)
    p.write_text(s,encoding='utf-8')
    print('All Customer Payment Link SMS option added')
else:
    print('All Customer Payment Link SMS option already present')
