from pathlib import Path

html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

# The app HTML is minified into one line. Replace the loader by locating its
# stable JavaScript markers instead of relying on a fragile regex.
start = s.find('let d;try{')
end_marker = 'if(!d)d=JSON.parse(JSON.stringify(DEF));'
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('Could not locate startup data loader in index.html')
end += len(end_marker)
loader = "let d;try{let raw='';try{raw=window.AndroidBridge&&AndroidBridge.loadData?AndroidBridge.loadData():''}catch(e){}if(!raw){let keys=[KEY,'star_communication_final_v2','star_communication_final_v1','star_communication'];for(let k of keys){try{raw=localStorage.getItem(k)||localStorage.getItem(k+'_backup')||''}catch(e){}if(raw)break}}d=raw?JSON.parse(raw):null}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));"
s = s[:start] + loader + s[end:]

# Persist to both localStorage and native app-private storage. APK updates keep
# app-private files, so customer data survives future installs/updates.
ss = s.find('function save(){')
if ss < 0:
    raise SystemExit('Could not locate save() in index.html')
se = s.find('}', ss)
if se < 0:
    raise SystemExit('Could not locate end of save() in index.html')
se += 1
save = "function save(){let z=JSON.stringify(d);try{localStorage.setItem(KEY,z);localStorage.setItem(KEY+'_backup',z)}catch(e){}try{if(window.AndroidBridge&&AndroidBridge.saveData)AndroidBridge.saveData(z)}catch(e){}}"
s = s[:ss] + save + s[se:]
html.write_text(s, encoding='utf-8')

java = Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
j = java.read_text(encoding='utf-8')

imports = 'import java.io.File;\nimport java.io.FileInputStream;\nimport java.io.FileOutputStream;\n'
if 'import java.io.File;' not in j:
    anchor = 'import android.widget.Toast;\n'
    if anchor in j:
        j = j.replace(anchor, anchor + imports, 1)
    else:
        j = imports + j
elif 'import java.io.FileInputStream;' not in j:
    j = j.replace('import java.io.File;\n', imports, 1)

if 'star_customer_data.json' not in j:
    needle = '    public class AppBridge {\n'
    if needle not in j:
        raise SystemExit('AppBridge class not found')
    methods = '''    public class AppBridge {\n        @JavascriptInterface public String loadData(){\n            try{\n                File f=new File(getFilesDir(),"star_customer_data.json");\n                if(!f.exists())return "";\n                FileInputStream in=new FileInputStream(f);\n                byte[] b=new byte[(int)f.length()];\n                int n=in.read(b); in.close();\n                return n>0?new String(b,java.nio.charset.StandardCharsets.UTF_8):"";\n            }catch(Exception e){return "";}\n        }\n        @JavascriptInterface public void saveData(String json){\n            if(json==null||json.isEmpty())return;\n            try{\n                File f=new File(getFilesDir(),"star_customer_data.json");\n                FileOutputStream out=new FileOutputStream(f);\n                out.write(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));\n                out.close();\n            }catch(Exception ignored){}\n        }\n'''
    j = j.replace(needle, methods, 1)

java.write_text(j, encoding='utf-8')
print('Update data migration patch fixed')