from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

js = r'''<script>
(function(){
  var BASE='https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html';
  function customerById(id){return (d.customers||[]).find(function(x){return String(x.id)===String(id);});}
  window.customerPaymentLink=function(id){
    var c=customerById(id); if(!c){toast('Customer not found');return '';}
    var params=new URLSearchParams();
    params.set('code',String(c.clientCode||c.id||''));
    params.set('name',String(c.name||'Customer'));
    params.set('location',String(c.address||c.location||''));
    params.set('package',String(c.pkg||c.packageName||c.package||''));
    params.set('bill',String(Number(c.fee||c.monthlyFee||0)));
    params.set('prev',String(Number(c.prevDue||0)));
    params.set('total',String(typeof due==='function'?due(c):(Number(c.prevDue||0)+Number(c.fee||c.monthlyFee||0))));
    params.set('merchant',String((d.settings&&d.settings.merchantNumber)||'01897-099850'));
    return BASE+'?'+params.toString();
  };
  window.copyCustomerPaymentLink=function(id){
    var link=customerPaymentLink(id); if(!link)return;
    if(navigator.clipboard){navigator.clipboard.writeText(link).then(function(){toast('Payment link copied');});}
    else {window.prompt('Copy payment link',link);}
  };
  window.sendCustomerPaymentLinkSMS=function(id){
    var c=customerById(id); if(!c||!c.phone){toast('Customer mobile number নেই');return;}
    var link=customerPaymentLink(id); var total=typeof due==='function'?due(c):(Number(c.prevDue||0)+Number(c.fee||c.monthlyFee||0));
    var msg='STAR COMMUNICATION\nClient Code: '+(c.clientCode||c.id)+'\nBill Due: '+money(total)+'\nPayment Link: '+link;
    try{
      if(window.AndroidBridge&&AndroidBridge.sendSmsFromSim2){AndroidBridge.sendSmsFromSim2(String(c.phone),msg);}
      else if(window.AndroidBridge&&AndroidBridge.sendSms){AndroidBridge.sendSms(String(c.phone),msg);}
      else {toast('SIM SMS is not available');return;}
      d.smsSentCount=Number(d.smsSentCount||0)+1; save(); toast('Payment link SMS sent');
    }catch(e){toast('SMS failed: '+(e.message||'unknown error'));}
  };
  function addButtons(){
    document.querySelectorAll('.customer').forEach(function(box){
      if(box.querySelector('.payment-link-actions'))return;
      var b=box.querySelector('button[onclick*="sendCustomerSMS"]'); if(!b)return;
      var m=String(b.getAttribute('onclick')||'').match(/sendCustomerSMS\(['"]([^'"]+)['"]\)/); if(!m)return;
      var id=m[1]; var wrap=document.createElement('div'); wrap.className='actions payment-link-actions';
      wrap.innerHTML='<button class="small" style="background:#7656d6;color:#fff" onclick="copyCustomerPaymentLink(\''+esc(id)+'\')">🔗 Copy Payment Link</button><button class="small" style="background:#0b2145;color:#fff" onclick="sendCustomerPaymentLinkSMS(\''+esc(id)+'\')">📨 Send Payment Link SMS</button>';
      box.appendChild(wrap);
    });
  }
  var oldRender=window.render;
  setInterval(addButtons,700);
  setTimeout(addButtons,200);
})();
</script>'''

if 'window.customerPaymentLink=function(id)' not in s:
    s=s.replace('</body>', js+'\n</body>', 1)
    print('Per-customer payment link actions added')
else:
    print('Per-customer payment link actions already present')
p.write_text(s, encoding='utf-8')
