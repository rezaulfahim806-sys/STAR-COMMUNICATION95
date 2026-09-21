from pathlib import Path
import re

html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

patch = r'''<script id="star-edit-sms-hardfix-20260921">
(function(){
  if(window.__starEditSmsHardfix20260921)return;
  window.__starEditSmsHardfix20260921=true;

  function store(){
    var x=null;
    try{x=JSON.parse(localStorage.getItem('star_communication_final_v2')||'null')}catch(e){x=null}
    if(!x){
      try{x=(typeof d!=='undefined'&&d)?d:null}catch(e){x=null}
    }
    if(!x)x={customers:[],payments:[],expenses:[],pending:[],history:[],settings:{}};
    if(!Array.isArray(x.customers))x.customers=[];
    return x;
  }
  function customer(id){
    var x=store(), sid=String(id==null?'':id);
    return x.customers.find(function(c){return String(c.id)==sid||String(c.clientCode||'')==sid;});
  }
  function field(id){
    var e=document.getElementById(id);
    return e?String(e.value==null?'':e.value):'';
  }
  function saveStore(x){
    localStorage.setItem('star_communication_final_v2',JSON.stringify(x));
    try{d=x}catch(e){}
    try{localStorage.setItem('star_communication_final_v2_last_backup',JSON.stringify({savedAt:new Date().toISOString(),data:x}))}catch(e){}
  }

  window.editCustomer=function(id){
    var c=customer(id);
    if(!c){toast('Customer not found');return false;}
    openSheet(
      '<h3>✏️ Edit Customer</h3>'+
      '<input id="hf_name" class="input" placeholder="Customer name" value="'+esc(c.name||'')+'">'+
      '<input id="hf_phone" class="input" placeholder="Mobile / WhatsApp" value="'+esc(c.phone||'')+'">'+
      '<input id="hf_address" class="input" placeholder="Address" value="'+esc(c.address||'')+'">'+
      '<input id="hf_pkg" class="input" placeholder="Package" value="'+esc(c.pkg||'')+'">'+
      '<input id="hf_fee" class="input" type="number" placeholder="Monthly fee" value="'+esc(c.fee||0)+'">'+
      '<input id="hf_pppoe" class="input" placeholder="PPPoE username" value="'+esc(c.pppoe||'')+'">'+
      '<input id="hf_pppoe_password" class="input" placeholder="PPPoE password" value="'+esc(c.pppoePassword||'')+'">'+
      '<input id="hf_onu" class="input" placeholder="ONU ID" value="'+esc(c.onu||'')+'">'+
      '<label class="muted">Connection Date</label><input id="hf_connection" class="input" type="date" value="'+esc(c.connectionDate||'')+'">'+
      '<label class="muted">Expiry Date</label><input id="hf_expiry" class="input" type="date" value="'+esc(c.expiry||'')+'">'+
      '<input id="hf_prev" class="input" type="number" placeholder="Previous due" value="'+esc(c.prevDue||0)+'">'+
      '<select id="hf_status" class="select">'+
        '<option value="active" '+(c.status==='active'?'selected':'')+'>Active</option>'+
        '<option value="inactive" '+(c.status==='inactive'?'selected':'')+'>Inactive</option>'+
        '<option value="expired" '+(c.status==='expired'?'selected':'')+'>Expired</option>'+
      '</select>'+
      '<button type="button" id="hf_save_btn" class="btn green full">💾 Save Changes</button>'+
      '<button type="button" class="btn light full" style="margin-top:7px" onclick="closeSheet()">Cancel</button>'
    );
    var b=document.getElementById('hf_save_btn');
    if(b)b.onclick=function(ev){if(ev)ev.preventDefault();return window.saveEditedCustomer(String(id));};
    return false;
  };

  window.saveEditedCustomer=function(id){
    var x=store(), c=x.customers.find(function(z){return String(z.id)==String(id)||String(z.clientCode||'')==String(id);});
    if(!c){toast('Customer not found');return false;}
    var name=field('hf_name'), phone=field('hf_phone');
    if(!name.trim()){toast('Customer name required');return false;}
    if(!phone.trim()){toast('Mobile number required');return false;}
    try{
      c.name=name.trim();
      c.phone=phone.trim();
      c.address=field('hf_address');
      c.pkg=field('hf_pkg');
      c.fee=Number(field('hf_fee')||0);
      c.pppoe=field('hf_pppoe');
      c.pppoePassword=field('hf_pppoe_password');
      c.onu=field('hf_onu');
      c.connectionDate=field('hf_connection')||c.connectionDate||today();
      c.expiry=field('hf_expiry');
      c.prevDue=Number(field('hf_prev')||0);
      c.status=field('hf_status')||c.status||'active';
      c.updatedAt=new Date().toISOString();
      saveStore(x);
      closeSheet();
      render();
      toast('Customer saved successfully');
    }catch(e){
      toast('Save failed');
    }
    return false;
  };

  window.starCustomerSms=function(id){
    var c=customer(id);
    if(!c){toast('Customer not found');return false;}
    var phone=String(c.phone||'').trim();
    if(!phone){toast('Customer mobile number নেই');return false;}
    var total=(typeof due==='function')?due(c):(Number(c.prevDue||0)+Number(c.fee||0));
    var msg='STAR COMMUNICATION\nCustomer: '+(c.name||'Customer')+'\nClient Code: '+(c.clientCode||c.id||'')+'\nMonthly Bill: '+money(c.fee)+'\nTotal Due: '+money(total);
    openSheet(
      '<h3>📩 Send SMS</h3>'+
      '<div class="muted">'+esc(c.name||'Customer')+' • '+esc(phone)+'</div>'+
      '<textarea id="hf_sms_text" class="input" rows="7" placeholder="Write message">'+esc(msg)+'</textarea>'+
      '<button type="button" id="hf_sms_send" class="btn dark full">📨 Send SMS</button>'+
      '<button type="button" class="btn light full" style="margin-top:7px" onclick="closeSheet()">Cancel</button>'+
      '<div class="muted" style="margin-top:8px">Send directly from the phone SIM. No SMS app/composer.</div>'
    );
    var b=document.getElementById('hf_sms_send');
    if(b)b.onclick=function(ev){if(ev)ev.preventDefault();return window.sendStarCustomerDirectSms(String(id));};
    return false;
  };

  window.sendStarCustomerDirectSms=function(id){
    var c=customer(id), msg=field('hf_sms_text').trim();
    if(!c||!c.phone){toast('Customer mobile number নেই');return false;}
    if(!msg){toast('Write a message first');return false;}
    try{
      if(window.AndroidBridge && typeof AndroidBridge.requestSmsPermission==='function'){
        AndroidBridge.requestSmsPermission();
      }
      if(window.AndroidBridge && typeof AndroidBridge.sendSmsDirect==='function'){
        AndroidBridge.sendSmsDirect(String(c.phone).trim(),msg);
        toast('SMS sending from SIM...');
        return false;
      }
      if(window.AndroidBridge && typeof AndroidBridge.sendSmsFromSim2==='function'){
        AndroidBridge.sendSmsFromSim2(String(c.phone).trim(),msg);
        toast('SMS sending from SIM...');
        return false;
      }
      toast('Direct SIM SMS service unavailable');
    }catch(e){toast('SMS failed');}
    return false;
  };
})();
</script>'''

if 'id="star-edit-sms-hardfix-20260921"' not in s:
    if '</body></html>' in s:
        s=s.replace('</body></html>',patch+'</body></html>')
    else:
        s+=patch
    html.write_text(s,encoding='utf-8')

java=Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
j=java.read_text(encoding='utf-8')

new_method = r'''        @JavascriptInterface public void requestSmsPermission(){
            runOnUiThread(() -> {
                if (Build.VERSION.SDK_INT < 23 || checkSelfPermission(Manifest.permission.SEND_SMS) == PackageManager.PERMISSION_GRANTED) {
                    Toast.makeText(MainActivity.this,"SMS permission already enabled",Toast.LENGTH_SHORT).show();
                    return;
                }
                MainActivity.this.requestSmsPermission();
            });
        }

        @JavascriptInterface public void sendSmsDirect(String phone,String message){
            String p=phone==null?"":phone.trim(), m=message==null?"":message.trim();
            if(p.isEmpty()||m.isEmpty())return;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                pendingSmsPhone=p; pendingSmsMessage=m;
                runOnUiThread(() -> requestSmsPermission());
                return;
            }
            sendDirectSms(p,m);
        }
'''

# Replace any existing direct-SMS bridge method so the hardfix is authoritative.
pat = r'        @JavascriptInterface public void sendSmsDirect\(String phone,String message\)\{.*?\n        \}\n(?=        @JavascriptInterface public boolean sendSms\()'
if re.search(pat,j,re.S):
    j=re.sub(pat,new_method,j,count=1,flags=re.S)
else:
    marker='        @JavascriptInterface public boolean sendSms(String phone,String message){'
    if marker not in j: raise SystemExit('sendSms marker not found')
    j=j.replace(marker,new_method+marker,1)

# Replace sendDirectSms with a no-composer, subscription-aware implementation.
pat2 = r'    private void sendDirectSms\(String phone,String message\) \{.*?\n    \}\n\n    private void sendBulkDirect'
method2 = r'''    private void sendDirectSms(String phone,String message) {
        final String p=phone==null?"":phone.trim();
        final String m=message==null?"":message.trim();
        if(p.isEmpty()||m.isEmpty()) return;
        try {
            SmsManager manager = null;
            if (Build.VERSION.SDK_INT >= 22) {
                try {
                    int subId = SubscriptionManager.getDefaultSmsSubscriptionId();
                    if (subId != SubscriptionManager.INVALID_SUBSCRIPTION_ID) {
                        if (Build.VERSION.SDK_INT >= 31) manager = SmsManager.getDefault().createForSubscriptionId(subId);
                        else manager = SmsManager.getSmsManagerForSubscriptionId(subId);
                    }
                } catch(Exception ignored) {}
            }
            if(manager==null) {
                try {
                    android.telephony.SubscriptionManager sm=(android.telephony.SubscriptionManager)getSystemService(TELEPHONY_SUBSCRIPTION_SERVICE);
                    java.util.List<android.telephony.SubscriptionInfo> infos=sm.getActiveSubscriptionInfoList();
                    if(infos!=null && !infos.isEmpty()) {
                        android.telephony.SubscriptionInfo info=infos.get(0);
                        int subId=info.getSubscriptionId();
                        if (Build.VERSION.SDK_INT >= 31) manager=SmsManager.getDefault().createForSubscriptionId(subId);
                        else if (Build.VERSION.SDK_INT >= 22) manager=SmsManager.getSmsManagerForSubscriptionId(subId);
                    }
                } catch(Exception ignored) {}
            }
            if(manager==null) manager=SmsManager.getDefault();

            java.util.ArrayList<String> parts=manager.divideMessage(m);
            if(parts!=null && parts.size()>1) manager.sendMultipartTextMessage(p,null,parts,null,null);
            else manager.sendTextMessage(p,null,m,null,null);

            runOnUiThread(()->{
                try{webView.evaluateJavascript("try{closeSheet();}catch(e){}",null);}catch(Exception ignored){}
                Toast.makeText(MainActivity.this,"SMS sent using SIM balance",Toast.LENGTH_SHORT).show();
            });
        } catch(Exception e) {
            runOnUiThread(()->Toast.makeText(MainActivity.this,"SIM SMS failed. Check SMS permission, SIM and balance.",Toast.LENGTH_LONG).show());
        }
    }

    private void sendBulkDirect'''
if not re.search(pat2,j,re.S):
    raise SystemExit('sendDirectSms block not found')
j=re.sub(pat2,method2,j,count=1,flags=re.S)
java.write_text(j,encoding='utf-8')
print('hardfix applied')

# Final Java cleanup: some older SMS patches can leave duplicate AppBridge methods.
def remove_duplicate_methods(src, signature):
    pos=[]
    start=0
    while True:
        i=src.find(signature,start)
        if i<0: break
        pos.append(i); start=i+len(signature)
    if len(pos)<=1: return src
    keep=pos[0]
    out=src
    for i in reversed(pos[1:]):
        brace=out.find('{',i)
        if brace<0: continue
        depth=0; end=None
        for k in range(brace,len(out)):
            if out[k]=='{': depth+=1
            elif out[k]=='}':
                depth-=1
                if depth==0:
                    end=k+1
                    if end<len(out) and out[end]=='\n': end+=1
                    break
        if end: out=out[:i]+out[end:]
    return out

j=remove_duplicate_methods(j, '@JavascriptInterface public boolean openSmsComposer(String phone,String message)')
j=remove_duplicate_methods(j, '@JavascriptInterface public void sendSmsDirect(String phone,String message)')
java.write_text(j,encoding='utf-8')
print('Removed duplicate SMS bridge methods if present.')
