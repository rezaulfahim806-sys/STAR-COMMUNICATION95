from pathlib import Path

# Native JSON backup prevents customer data from disappearing if WebView localStorage is lost.
html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

old_init = "let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));"
new_init = "let d;try{let native='';try{native=window.AndroidBridge&&AndroidBridge.loadData?AndroidBridge.loadData():''}catch(e){}d=JSON.parse(native||localStorage.getItem(KEY)||localStorage.getItem(KEY+'_backup')||'null')}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));"
if old_init in s:
    s = s.replace(old_init, new_init, 1)

old_save = "function save(){localStorage.setItem(KEY,JSON.stringify(d))}"
new_save = "function save(){let z=JSON.stringify(d);localStorage.setItem(KEY,z);try{localStorage.setItem(KEY+'_backup',z)}catch(e){}try{if(window.AndroidBridge&&AndroidBridge.saveData)AndroidBridge.saveData(z)}catch(e){}}"
if old_save in s:
    s = s.replace(old_save, new_save, 1)

s = s.replace("function fixExpiry(){let ch=false;d.customers.forEach(c=>{if(c.expiry&&c.expiry<today()&&c.status!=='expired'){c.status='expired';ch=true}});if(ch)save()}",
              "function fixExpiry(){let ch=false;d.customers.forEach(c=>{if(c.expiry&&c.expiry<today()&&c.status!=='expired'){c.status='expired';c.expiredAt=today();ch=true}});if(ch)save()}")

html.write_text(s, encoding='utf-8')

java = Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
j = java.read_text(encoding='utf-8')

if 'import java.io.File;' not in j:
    j = j.replace('import android.widget.Toast;\n', 'import android.widget.Toast;\nimport java.io.File;\n', 1)
if 'import java.io.FileInputStream;' not in j:
    j = j.replace('import android.widget.Toast;\n', 'import android.widget.Toast;\nimport java.io.FileInputStream;\n', 1)
if 'import java.io.FileOutputStream;' not in j:
    j = j.replace('import android.widget.Toast;\n', 'import android.widget.Toast;\nimport java.io.FileOutputStream;\n', 1)

needle = '    public class AppBridge {\n'
methods = '''    public class AppBridge {\n        @JavascriptInterface public String loadData(){\n            try{\n                File f=new File(getFilesDir(),"star_customer_data.json");\n                if(!f.exists())return "";\n                FileInputStream in=new FileInputStream(f);\n                byte[] b=new byte[(int)f.length()];\n                int n=in.read(b); in.close();\n                return new String(b,java.nio.charset.StandardCharsets.UTF_8);\n            }catch(Exception e){return "";}\n        }\n        @JavascriptInterface public void saveData(String json){\n            if(json==null)return;\n            try{\n                FileOutputStream out=new FileOutputStream(new File(getFilesDir(),"star_customer_data.json"));\n                out.write(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));\n                out.close();\n            }catch(Exception ignored){}\n        }\n'''
if 'star_customer_data.json' not in j:
    if needle not in j:
        raise SystemExit('AppBridge class not found')
    j = j.replace(needle, methods, 1)

java.write_text(j, encoding='utf-8')
print('Native customer persistence applied')
