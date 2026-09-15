from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

s = s.replace(
'''<button class="small" style="background:#1677d2;color:#fff" onclick="sendCustomerSMS('${c.id}')">📨 Send SMS</button>${dv>0?`<button class="small pay" onclick="payCustomer('${c.id}')">Pay</button>`:''}''',
'''<button class="small" style="background:#1677d2;color:#fff" onclick="sendCustomerSMS('${c.id}')">📨 Send SMS</button><button class="small" style="background:#7656d6;color:#fff" onclick="generatePaymentLink('${c.id}')">🔗 Payment Link</button>${dv>0?`<button class="small pay" onclick="payCustomer('${c.id}')">Pay</button>`:''}''')

insert = r'''<script>
(function(){
  var PAYMENT_BASE='https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html';
  function paymentLinkFor(c){
    var q=new URLSearchParams();
    q.set('code',String(c.clientCode||c.id||''));
    q.set('name',String(c.name||''));
    q.set('location',String(c.address||c.location||''));
    q.set('package',String(c.pkg||c.packageName||''));
    q.set('bill',String(Number(c.fee||c.monthlyFee||0)));
    q.set('previousDue',String(Number(c.prevDue||0)));
    q.set('totalDue',String(typeof due==='function'?due(c):Number(c.prevDue||0)+Number(c.fee||0)));
    q.set('merchant',String((d.settings&&d.settings.merchantNumber)||'01897-099850'));
    return PAYMENT_BASE+'?'+q.toString();
  }
  window.customerPaymentLink=paymentLinkFor;
  window.generatePaymentLink=function(id){
    var c=d.customers.find(function(x){return String(x.id)===String(id);});
    if(!c){toast('Customer not found');return;}
    var link=paymentLinkFor(c);
    openSheet('<h3>🔗 Customer Payment Link</h3><div class="muted">'+esc(c.clientCode||'')+' • '+esc(c.name||'')+'</div><input id="customerPayLink" class="input" readonly value="'+esc(link)+'"><button class="btn full" onclick="copyCustomerPaymentLink()">📋 Copy Link</button><button class="btn green full" style="margin-top:7px" onclick="sendPaymentLinkSMS(\''+String(c.id).replace(/'/g,"\\'")+"\')">📨 Send Payment Link SMS</button><button class="btn light full" style="margin-top:7px" onclick="closeSheet()">Close</button>');
  };
  window.copyCustomerPaymentLink=function(){
    var e=document.getElementById('customerPayLink');if(!e)return;
    if(navigator.clipboard){navigator.clipboard.writeText(e.value).then(function(){toast('Payment link copied');});}
    else {e.select();document.execCommand('copy');toast('Payment link copied');}
  };
  window.sendPaymentLinkSMS=function(id){
    var c=d.customers.find(function(x){return String(x.id)===String(id);});
    if(!c||!c.phone){toast('Customer mobile number নেই');return;}
    var link=paymentLinkFor(c);
    var total=typeof due==='function'?due(c):Number(c.prevDue||0)+Number(c.fee||0);
    var msg='STAR COMMUNICATION: '+(c.name||'Customer')+' আপনার বিল পরিশোধ করুন। Client Code: '+(c.clientCode||c.id)+'. Total Due: '+money(total)+'. Payment Link: '+link;
    try{
      if(window.AndroidBridge&&AndroidBridge.sendSmsFromSim2)AndroidBridge.sendSmsFromSim2(String(c.phone),msg);
      else if(window.AndroidBridge&&AndroidBridge.sendSms)AndroidBridge.sendSms(String(c.phone),msg);
      else {toast('SIM SMS is not available');return;}
      d.smsSentCount=Number(d.smsSentCount||0)+1;save();closeSheet();toast('Payment link SMS sent');
    }catch(e){toast('SMS failed: '+(e.message||'unknown error'));}
  };
})();
</script>
'''
if 'window.customerPaymentLink=paymentLinkFor' not in s:
    s=s.replace('</body>',insert+'</body>',1)

p.write_text(s,encoding='utf-8')
print('Customer payment link generate/copy/SMS actions added')
