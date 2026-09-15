from pathlib import Path

html=Path('app/src/main/assets/index.html')
s=html.read_text(encoding='utf-8')

# Put one final, authoritative implementation after all older payment-link patches.
script=r'''<script>
(function(){
  function findCustomer(id){
    var list=(window.d&&Array.isArray(d.customers))?d.customers:[];
    var sid=String(id==null?'':id);
    return list.find(function(c){return String(c.id)===sid||String(c.clientCode||'')===sid;});
  }
  function linkFor(c){
    var code=String(c.clientCode||c.id||'');
    var q=new URLSearchParams();
    q.set('code',code);q.set('name',String(c.name||'Customer'));
    q.set('location',String(c.address||c.location||''));
    q.set('package',String(c.pkg||c.packageName||''));
    q.set('bill',String(Number(c.fee||c.monthlyFee||0)));
    q.set('prev',String(Number(c.prevDue||c.previousDue||0)));
    q.set('total',String(typeof due==='function'?due(c):Number(c.prevDue||c.previousDue||0)+Number(c.fee||c.monthlyFee||0)));
    q.set('merchant',String((d.settings&&d.settings.merchantNumber)||'01897-099850'));
    return 'https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html?'+q.toString();
  }
  window.__starPaymentCustomerId=null;
  window.generatePaymentLink=function(id){
    var c=findCustomer(id);
    if(!c){toast('Customer not found');return;}
    window.__starPaymentCustomerId=String(c.id);
    var link=linkFor(c);
    openSheet('<h3>🔗 Payment Link</h3><div class="muted">'+esc(c.clientCode||'')+' • '+esc(c.name||'')+'</div><textarea id="customerPayLink" class="input" readonly rows="3" style="resize:none">'+esc(link)+'</textarea><button class="btn full" onclick="copyCustomerPaymentLink()">📋 Copy Link</button><button class="btn dark full" style="margin-top:7px" onclick="sendPaymentLinkSMS()">📨 Send Msg</button><button class="btn light full" style="margin-top:7px" onclick="openCustomerPaymentPage()">🌐 Open Payment Page</button>');
  };
  window.copyCustomerPaymentLink=function(){
    var e=document.getElementById('customerPayLink');
    if(!e){toast('Payment link not ready');return;}
    var link=String(e.value||'').trim();
    if(!link){toast('Payment link not ready');return;}
    try{
      if(window.AndroidBridge&&AndroidBridge.copyText){AndroidBridge.copyText(link);toast('Payment link copied');return;}
    }catch(err){}
    try{
      e.focus();e.select();e.setSelectionRange(0,e.value.length);
      var ok=document.execCommand('copy');
      if(ok){toast('Payment link copied');return;}
    }catch(err){}
    toast('Copy failed — long press the link to copy');
  };
  window.sendPaymentLinkSMS=function(){
    var c=findCustomer(window.__starPaymentCustomerId);
    if(!c){toast('Customer not found');return;}
    if(!c.phone){toast('Customer mobile number নেই');return;}
    var link=linkFor(c), total=typeof due==='function'?due(c):Number(c.prevDue||c.previousDue||0)+Number(c.fee||c.monthlyFee||0);
    var msg='STAR COMMUNICATION\nCustomer: '+(c.name||'Customer')+'\nClient Code: '+(c.clientCode||c.id)+'\nTotal Due: '+money(total)+'\nPayment Link: '+link;
    try{
      if(window.AndroidBridge&&AndroidBridge.openSmsComposer){AndroidBridge.openSmsComposer(String(c.phone).trim(),msg);toast('SMS app opened — choose SIM 2 and Send');return;}
      location.href='smsto:'+encodeURIComponent(String(c.phone).trim())+'?body='+encodeURIComponent(msg);
    }catch(err){toast('SMS app could not be opened');}
  };
  window.openCustomerPaymentPage=function(){
    var e=document.getElementById('customerPayLink');
    if(e&&e.value)location.href=e.value;
  };
})();
</script>
'''
if 'window.__starPaymentCustomerId' not in s:
    s=s.replace('</body>',script+'</body>',1)
html.write_text(s,encoding='utf-8')

java=Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
j=java.read_text(encoding='utf-8')
# Add imports for clipboard and SMS compose.
j=j.replace('import android.content.Intent;','import android.content.Intent;\nimport android.content.ClipData;\nimport android.content.ClipboardManager;',1)
# Intercept SMS schemes so WebView never tries to load sms: as a web URL.
old='''    private boolean handleUrl(String u){
        if(u.startsWith("tel:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")){try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(u)));}catch(Exception ignored){}return true;} return false;
    }'''
new='''    private boolean handleUrl(String u){
        if(u.startsWith("tel:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")){try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(u)));}catch(Exception ignored){}return true;}
        if(u.startsWith("sms:")||u.startsWith("smsto:")||u.startsWith("mmsto:")){try{Intent i=new Intent(Intent.ACTION_SENDTO,Uri.parse(u));startActivity(i);}catch(Exception ignored){}return true;}
        return false;
    }'''
if old not in j: raise SystemExit('handleUrl block not found')
j=j.replace(old,new,1)
# Add clipboard and SMS composer bridge methods before scheduleExpiry.
needle='''        @JavascriptInterface public void scheduleExpiry(String phone,String name,String expiry){AutoMessageReceiver.scheduleExpiry(MainActivity.this,phone,name,expiry);}'''
insert='''        @JavascriptInterface public void copyText(String text){
            if(text==null)return;
            ClipboardManager cm=(ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("STAR COMMUNICATION Payment Link",text));
        }
        @JavascriptInterface public void openSmsComposer(String phone,String message){
            try{
                Uri uri=Uri.parse("smsto:"+Uri.encode(phone==null?"":phone));
                Intent i=new Intent(Intent.ACTION_SENDTO,uri);
                i.putExtra("sms_body",message==null?"":message);
                startActivity(i);
            }catch(Exception e){
                runOnUiThread(()->Toast.makeText(MainActivity.this,"No SMS app available",Toast.LENGTH_LONG).show());
            }
        }
        @JavascriptInterface public void scheduleExpiry(String phone,String name,String expiry){AutoMessageReceiver.scheduleExpiry(MainActivity.this,phone,name,expiry);}'''
if needle not in j: raise SystemExit('bridge insertion point not found')
j=j.replace(needle,insert,1)
# Make Android Back return from remote payment page to app/customer screen.
start=j.find('    @Override public void onBackPressed()')
if start<0: raise SystemExit('onBackPressed not found')
end=j.find('\n',start)
if end<0:end=len(j)
j=j[:start]+'''    @Override public void onBackPressed(){
        if(webView!=null){
            if(webView.canGoBack()){webView.goBack();}
            else {webView.evaluateJavascript("typeof appBack==='function' ? appBack() : null",null);}
        } else super.onBackPressed();
    }'''+j[end:]
java.write_text(j,encoding='utf-8')
print('final payment actions and native SMS/clipboard/back patched')
