from pathlib import Path
import re
p=Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
s=p.read_text(encoding="utf-8")

old='''@JavascriptInterface public boolean sendSms(String phone,String message){
            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty())return false;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(() -> { Toast.makeText(MainActivity.this,"SMS permission required. Allow it, then press Send SMS again.",Toast.LENGTH_LONG).show(); requestSmsPermission(); });
                return false;
            }
            try{
                SmsManager sms = SmsManager.getDefault();
                sms.sendTextMessage(phone.trim(),null,message,null,null);
                runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS sent using SIM balance",Toast.LENGTH_SHORT).show());
                return true;
            }catch(SecurityException e){runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS permission denied by Android",Toast.LENGTH_LONG).show());return false;}
            catch(Exception e){runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS failed: check SIM/network/balance",Toast.LENGTH_LONG).show());return false;}
        }'''
new='''@JavascriptInterface public boolean sendSms(String phone,String message){
            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty())return false;
            String p=phone.trim(), m=message.trim();
            try{
                if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) == PackageManager.PERMISSION_GRANTED) {
                    SmsManager.getDefault().sendTextMessage(p,null,m,null,null);
                    runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS sent using SIM",Toast.LENGTH_SHORT).show());
                    return true;
                }
            }catch(Exception ignored){}
            // Reliable fallback: open the phone's SMS composer. This works even when SEND_SMS permission is unavailable.
            try{
                Intent i=new Intent(Intent.ACTION_SENDTO,Uri.parse("smsto:"+Uri.encode(p)));
                i.putExtra("sms_body",m);
                startActivity(i);
                return true;
            }catch(Exception e){
                runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS app not available",Toast.LENGTH_LONG).show());
                return false;
            }
        }'''
if old not in s:
    raise SystemExit("sendSms block not found")
s=s.replace(old,new,1)
old2='''if(u.startsWith("tel:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")||u.startsWith("https://"))'''
new2='''if(u.startsWith("tel:")||u.startsWith("sms:")||u.startsWith("smsto:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")||u.startsWith("https://"))'''
if old2 in s:
    s=s.replace(old2,new2,1)
else:
    raise SystemExit("handleUrl block not found")
p.write_text(s,encoding="utf-8")
print("SMS button hardened")
