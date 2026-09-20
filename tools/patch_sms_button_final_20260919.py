from pathlib import Path
import re
p=Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
s=p.read_text(encoding="utf-8")

new='''@JavascriptInterface public boolean openSmsComposer(String phone,String message){
            if(phone==null||phone.trim().isEmpty())return false;
            final String p=phone.trim(), m=message==null?"":message.trim();
            try{
                Intent i=new Intent(Intent.ACTION_SENDTO,Uri.parse("smsto:"+Uri.encode(p)));
                if(!m.isEmpty()) i.putExtra("sms_body",m);
                try{
                    startActivity(i);
                    return true;
                }catch(Exception first){
                    try{
                        Intent v=new Intent(Intent.ACTION_VIEW,Uri.parse("sms:"+Uri.encode(p)));
                        if(!m.isEmpty()) v.putExtra("sms_body",m);
                        startActivity(v);
                        return true;
                    }catch(Exception second){
                        runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS app could not be opened.",Toast.LENGTH_LONG).show());
                        return false;
                    }
                }
            }catch(Exception e){
                runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS app could not be opened.",Toast.LENGTH_LONG).show());
                return false;
            }
        }
        @JavascriptInterface public boolean sendSms(String phone,String message){
            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty())return false;
            final String p=phone.trim(), m=message.trim();
            if(Build.VERSION.SDK_INT>=23 && checkSelfPermission(Manifest.permission.SEND_SMS)==PackageManager.PERMISSION_GRANTED){
                sendDirectSms(p,m);
                return true;
            }
            return openSmsComposer(p,m);
        }'''

pat=re.compile(r'@JavascriptInterface public boolean sendSms\(String phone,String message\)\{.*?\n        \}\n        @JavascriptInterface public void sendBulk',re.S)
m=pat.search(s)
if m:
    s=s[:m.start()]+new+'\n        @JavascriptInterface public void sendBulk'+s[m.end():]
elif new not in s:
    raise SystemExit("sendSms method not found")

if 'u.startsWith("sms:")||u.startsWith("smsto:")' not in s:
    marker='if(u.startsWith("tel:")'
    pos=s.find(marker)
    if pos>=0:
        line_start=s.rfind('\n',0,pos)+1
        line_end=s.find('\n',pos)
        if line_end<0: line_end=len(s)
        line=s[line_start:line_end]
        line=line.replace('u.startsWith("tel:")','u.startsWith("tel:")||u.startsWith("sms:")||u.startsWith("smsto:")',1)
        s=s[:line_start]+line+s[line_end:]
    else:
        print("handleUrl SMS scheme patch skipped; direct bridge handles SMS")

p.write_text(s,encoding="utf-8")
print("SMS button hardened")
