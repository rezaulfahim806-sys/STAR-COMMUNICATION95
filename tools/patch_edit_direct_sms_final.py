from pathlib import Path

# Final narrow fix: customer Edit + editable direct-SIM SMS composer.
html=Path('app/src/main/assets/index.html')
s=html.read_text(encoding='utf-8')
patch=r'''<script id="star-edit-direct-sms-final">
(function(){
  if(window.__starEditDirectSmsFinal)return;
  window.__starEditDirectSmsFinal=true;
  function findCustomer(id){
    return (d.customers||[]).find(function(c){return String(c.id)===String(id)||String(c.clientCode||'')===String(id);});
  }
  window.editCustomer=function(id){
    var c=findCustomer(id);
    if(!c){toast('Customer not found');return;}
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
    var c=findCustomer(id);
    if(!c){toast('Customer not found');return;}
    var name=(document.getElementById('ec_name')||{}).value||'';
    var phone=(document.getElementById('ec_phone')||{}).value||'';
    if(!name.trim()||!phone.trim()){toast('Name and mobile required');return;}
    c.name=name.trim();c.phone=phone.trim();
    c.address=(document.getElementById('ec_address')||{}).value||'';
    c.pkg=(document.getElementById('ec_pkg')||{}).value||'';
    c.fee=Number((document.getElementById('ec_fee')||{}).value||0);
    c.pppoe=(document.getElementById('ec_pp')||{}).value||'';
    c.pppoePassword=(document.getElementById('ec_pw')||{}).value||'';
    c.onu=(document.getElementById('ec_onu')||{}).value||'';
    c.connectionDate=(document.getElementById('ec_cd')||{}).value||c.connectionDate||today();
    c.expiry=(document.getElementById('ec_ex')||{}).value||'';
    c.prevDue=Number((document.getElementById('ec_prev')||{}).value||0);
    c.status=(document.getElementById('ec_st')||{}).value||'active';
    c.updatedAt=new Date().toISOString();
    save();closeSheet();render();toast('Customer updated');
  };
  window.starCustomerSms=function(id){
    var c=findCustomer(id);
    if(!c){toast('Customer not found');return;}
    if(!c.phone){toast('Customer mobile number নেই');return;}
    var defaultMsg='STAR COMMUNICATION\\nCustomer: '+(c.name||'Customer')+'\\nClient Code: '+(c.clientCode||c.id||'')+'\\nMonthly Bill: '+money(c.fee)+'\\nTotal Due: '+money(typeof due==='function'?due(c):Number(c.prevDue||0)+Number(c.fee||0));
    openSheet('<h3>📩 Send SMS</h3><div class="muted">'+esc(c.name||'Customer')+' • '+esc(c.phone)+'</div><textarea id="starSmsText" class="input" rows="7" placeholder="Write message">'+esc(defaultMsg)+'</textarea><button class="btn dark full" onclick="sendStarCustomerDirectSms('+JSON.stringify(String(id))+')">📨 Send Direct SIM SMS</button><button class="btn light full" style="margin-top:7px" onclick="closeSheet()">Cancel</button><div class="muted" style="margin-top:8px">SMS will be sent directly from the phone SIM. SMS balance may be charged by your mobile operator.</div>');
  };
  window.sendStarCustomerDirectSms=function(id){
    var c=findCustomer(id),el=document.getElementById('starSmsText');
    var msg=el?String(el.value||'').trim():'';
    if(!c||!c.phone){toast('Customer mobile number নেই');return;}
    if(!msg){toast('Write a message first');return;}
    try{
      if(window.AndroidBridge&&typeof AndroidBridge.sendSmsDirect==='function'){
        AndroidBridge.sendSmsDirect(String(c.phone).trim(),msg);
        d.smsSentCount=Number(d.smsSentCount||0)+1;save(false);
        return;
      }
      toast('Direct SIM SMS service unavailable');
    }catch(e){toast('SMS failed: '+(e.message||'unknown error'));}
  };
})();
</script>'''
if 'id="star-edit-direct-sms-final"' not in s:
    s=s.replace('</body></html>',patch+'</body></html>')
html.write_text(s,encoding='utf-8')

java=Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
j=java.read_text(encoding='utf-8')
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
if 'sendSmsDirect(String phone,String message)' not in j:
    j=j.replace(marker,method+marker)
java.write_text(j,encoding='utf-8')
print('Final Edit + direct SIM SMS patch applied')
