from pathlib import Path
p=Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
s=p.read_text(encoding='utf-8')
if 'import android.telephony.SubscriptionManager;' not in s:
    s=s.replace('import android.telephony.SmsManager;','import android.telephony.SmsManager;\nimport android.telephony.SubscriptionInfo;\nimport android.telephony.SubscriptionManager;\nimport java.util.List;')
marker='        @JavascriptInterface public void sendSms(String phone,String message){'
method='''        @JavascriptInterface public void sendSmsFromSim2(String phone,String message){
            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty())return;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(() -> { Toast.makeText(MainActivity.this,"SMS permission is required for SIM 2 SMS.",Toast.LENGTH_LONG).show(); requestSmsPermission(); });
                return;
            }
            try {
                SubscriptionManager sm=(SubscriptionManager)getSystemService(TELEPHONY_SUBSCRIPTION_SERVICE);
                List<SubscriptionInfo> infos=sm.getActiveSubscriptionInfoList();
                SubscriptionInfo sim2=null;
                if(infos!=null){ for(SubscriptionInfo info:infos){ if(info.getSimSlotIndex()==1){ sim2=info; break; } } }
                if(sim2==null){ runOnUiThread(() -> Toast.makeText(MainActivity.this,"SIM 2 Robi is not active.",Toast.LENGTH_LONG).show()); return; }
                int subId=sim2.getSubscriptionId();
                SmsManager sms;
                if(Build.VERSION.SDK_INT>=31) sms=SmsManager.createForSubscriptionId(subId);
                else sms=SmsManager.getSmsManagerForSubscriptionId(subId);
                sms.sendTextMessage(phone.trim(),null,message,null,null);
                runOnUiThread(() -> Toast.makeText(MainActivity.this,"SMS sent from SIM 2 (Robi)",Toast.LENGTH_SHORT).show());
            } catch(Exception e){ runOnUiThread(() -> Toast.makeText(MainActivity.this,"SIM 2 SMS failed: check SIM/network/balance",Toast.LENGTH_LONG).show()); }
        }
'''
if 'sendSmsFromSim2' not in s:
    s=s.replace(marker,method+marker)
p.write_text(s,encoding='utf-8')
print('SIM 2 SMS patch applied')
