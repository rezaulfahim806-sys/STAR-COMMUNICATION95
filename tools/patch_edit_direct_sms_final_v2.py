from pathlib import Path

html=Path('app/src/main/assets/index.html')
s=html.read_text(encoding='utf-8')
patch=r'''<script id="star-edit-direct-sms-final-v2">
(function(){
  if(window.__starEditDirectSmsFinalV2)return;
  window.__starEditDirectSmsFinalV2=true;
  function findCustomer(id){return (d.customers||[]).find(function(c){return String(c.id)===String(id)||String(c.clientCode||'')===String(id);});}
  window.editCustomer=function(id){
    var c=findCustomer(id); if(!c){toast('Customer not found');return;}
    openSheet('<h3>✏️ Edit Customer</h3>'+
      '<input id="ec_name" class="input" placeholder="Customer name" value="'+esc(c.name||'')+'">'+
      '<input id="ec_phone" class="input" placeholder="Mobile / WhatsApp" value="'+esc(c.phone||'')+'">'+
      '<input id="ec_address" class="input" placeholder="Address" value="'+esc(c.address||'')+'">'+
      '<input id="ec_pkg" class="input" placeholder="Package" value="'+esc(c.pkg||'')+'">'+
      '<input id="ec_fee" class="input" type="number" placeholder="Monthly fee" value="'+esc(c.fee||0)+'">'+
      '<input id="ec_pp" class="input" placeholder="PPPoE username" value="'+esc(c.pppoe||'')+'">'+
      '<input id="ec_pw" class="input" placeholder="PPPoE password" value="'+esc(c.pppoePassword||'')+'">'+
      '<input id="ec_onu" class="input" placeholder="ONU ID" value="'+esc(c.onu||'')+'">'+
      '<label class="muted">Connection Date</label><input id="ec_cd" class="input" type="date" value="'+esc(c.connectionDate||'')+'">'+
      '<label class="muted">Expiry Date</label><input id="ec_ex" class="input" type="date" value="'+esc(c.expiry||'')+'">'+
      '<input id="ec_prev" class="input" type="number" placeholder="Previous due" value="'+esc(c.prevDue||0)+'">'+
      '<select id="ec_st" class="select"><option value="active" '+(c.status==='active'?'selected':'')+'>Active</option><option value="inactive" '+(c.status==='inactive'?'selected':'')+'>Inactive</option><option value="expired" '+(c.status==='expired'?'selected':'')+'>Expired</option></select>'+
      '<button class="btn green full" onclick="saveEditedCustomer('+JSON.stringify(String(id))+')">💾 Save Changes</button>'+
      '<button class="btn light full" style="margin-top:7px" onclick="closeSheet()">Cancel</button>');
  };
  window.saveEditedCustomer=function(id){
    var c=findCustomer(id); if(!c){toast('Customer not found');return;}
    var val=function(x){var e=document.getElementById(x);return e?e.value:'';};
    if(!String(val('ec_name')).trim()||!String(val('ec_phone')).trim()){toast('Name and mobile required');return;}
    c.name=String(val('ec_name')).trim(); c.phone=String(val('ec_phone')).trim(); c.address=val('ec_address'); c.pkg=val('ec_pkg');
    c.fee=Number(val('ec_fee')||0); c.pppoe=val('ec_pp'); c.pppoePassword=val('ec_pw'); c.onu=val('ec_onu');
    c.connectionDate=val('ec_cd')||c.connectionDate||today(); c.expiry=val('ec_ex'); c.prevDue=Number(val('ec_prev')||0); c.status=val('ec_st')||'active';
    c.updatedAt=new Date().toISOString(); save(); closeSheet(); render(); toast('Customer updated');
  };
  window.starCustomerSms=function(id){
    var c=findCustomer(id); if(!c){toast('Customer not found');return;} if(!c.phone){toast('Customer mobile number নেই');return;}
    var total=(typeof due==='function')?due(c):(Number(c.prevDue||0)+Number(c.fee||0));
    var msg='STAR COMMUNICATION\\nCustomer: '+(c.name||'Customer')+'\\nClient Code: '+(c.clientCode||c.id||'')+'\\nMonthly Bill: '+money(c.fee)+'\\nTotal Due: '+money(total);
    openSheet('<h3>📩 Send SMS</h3><div class="muted">'+esc(c.name||'Customer')+' • '+esc(c.phone)+'</div><textarea id="starSmsText" class="input" rows="7" placeholder="Write message">'+esc(msg)+'</textarea><button class="btn dark full" onclick="sendStarCustomerDirectSms('+JSON.stringify(String(id))+')">📨 Send Direct SIM SMS</button><button class="btn light full" style="margin-top:7px" onclick="closeSheet()">Cancel</button><div class="muted" style="margin-top:8px">SMS goes directly from the phone SIM.</div>');
  };
  window.sendStarCustomerDirectSms=function(id){
    var c=findCustomer(id), e=document.getElementById('starSmsText'), msg=e?String(e.value||'').trim():'';
    if(!c||!c.phone){toast('Customer mobile number নেই');return;} if(!msg){toast('Write a message first');return;}
    try{
      if(window.AndroidBridge&&typeof AndroidBridge.sendSmsDirect==='function'){
        AndroidBridge.sendSmsDirect(String(c.phone).trim(),msg);
        d.smsSentCount=Number(d.smsSentCount||0)+1; save(false); toast('SMS sending...');
      }else toast('Direct SIM SMS service unavailable');
    }catch(err){toast('SMS failed: '+(err.message||'unknown error'));}
  };
})();
</script>'''
if 'id="star-edit-direct-sms-final-v2"' not in s:
    s += patch
html.write_text(s,encoding='utf-8')

java=Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
j=java.read_text(encoding='utf-8')
if 'sendSmsDirect(String phone,String message)' not in j:
    marker='        @JavascriptInterface public boolean sendSms(String phone,String message){'
    method='''        @JavascriptInterface public void sendSmsDirect(String phone,String message){
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
    if marker not in j:
        raise SystemExit('sendSms marker not found')
    j=j.replace(marker,method+marker)
    java.write_text(j,encoding='utf-8')
print('v2 patch applied')
