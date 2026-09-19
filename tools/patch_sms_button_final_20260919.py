from pathlib import Path
import re
p=Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
s=p.read_text(encoding="utf-8")

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

# Replace any existing sendSms method inside AppBridge.
pat=re.compile(r'@JavascriptInterface public boolean sendSms\(String phone,String message\)\{.*?\n        \}\n        @JavascriptInterface public void sendBulk',re.S)
m=pat.search(s)
if m:
    s=s[:m.start()]+new+'\n        @JavascriptInterface public void sendBulk'+s[m.end():]
elif new not in s:
    raise SystemExit("sendSms method not found")

# Allow SMS schemes if the URL handler is present; tolerate earlier handler variants.
if 'u.startsWith("sms:")||u.startsWith("smsto:")' not in s:
    marker='if(u.startsWith("tel:")'
    pos=s.find(marker)
    if pos>=0:
        end=s.find('))',pos)
        # Simpler targeted replacement of the known first condition line.
        line_start=s.rfind('\n',0,pos)+1
        line_end=s.find('\n',pos)
        line=s[line_start:line_end]
        line=line.replace('u.startsWith("tel:")','u.startsWith("tel:")||u.startsWith("sms:")||u.startsWith("smsto:")',1)
        s=s[:line_start]+line+s[line_end:]
    else:
        raise SystemExit("handleUrl condition not found")

p.write_text(s,encoding="utf-8")
print("SMS button hardened")
