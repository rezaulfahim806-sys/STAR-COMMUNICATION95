from pathlib import Path
import re

# Preserve customer/billing data across APK updates. Older builds used v1/localStorage;
# newer builds use v2. Do not depend on one exact previous patch string because the
# build applies several source patches in sequence.
html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

# Replace the complete startup data-loader block, whether it is the original loader
# or a partially patched loader.
loader_re = re.compile(r"let d;try\{.*?\}catch\(e\)\{d=null\}if\(!d\)d=JSON\.parse\(JSON\.stringify\(DEF\)\);", re.S)
loader = """let d;try{let raw='';try{raw=window.AndroidBridge&&AndroidBridge.loadData?AndroidBridge.loadData():''}catch(e){}if(!raw){let keys=[KEY,'star_communication_final_v2','star_communication_final_v1','star_communication'];for(let k of keys){try{raw=localStorage.getItem(k)||localStorage.getItem(k+'_backup')||''}catch(e){}if(raw)break}}d=raw?JSON.parse(raw):null}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));"""
s, n = loader_re.subn(loader, s, count=1)
if n == 0:
    raise SystemExit('Could not locate startup data loader in index.html')

# Replace save() with a version that keeps the current localStorage key and also
# writes a native Android file. This native file survives normal APK updates.
save_re = re.compile(r"function save\(\)\{.*?\}", re.S)
save = "function save(){let z=JSON.stringify(d);try{localStorage.setItem(KEY,z);localStorage.setItem(KEY+'_backup',z)}catch(e){}try{if(window.AndroidBridge&&AndroidBridge.saveData)AndroidBridge.saveData(z)}catch(e){}}"
# Only replace the first function named save().
m = save_re.search(s)
if not m:
    raise SystemExit('Could not locate save() in index.html')
s = s[:m.start()] + save + s[m.end():]

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

# Add native persistence methods inside AppBridge if they are not already present.
if 'star_customer_data.json' not in j:
    needle = '    public class AppBridge {\n'
    if needle not in j:
        raise SystemExit('AppBridge class not found')
    methods = '''    public class AppBridge {\n        @JavascriptInterface public String loadData(){\n            try{\n                File f=new File(getFilesDir(),"star_customer_data.json");\n                if(!f.exists())return "";\n                FileInputStream in=new FileInputStream(f);\n                byte[] b=new byte[(int)f.length()];\n                int n=in.read(b); in.close();\n                return n>0?new String(b,java.nio.charset.StandardCharsets.UTF_8):"";\n            }catch(Exception e){return "";}\n        }\n        @JavascriptInterface public void saveData(String json){\n            if(json==null||json.isEmpty())return;\n            try{\n                File f=new File(getFilesDir(),"star_customer_data.json");\n                FileOutputStream out=new FileOutputStream(f);\n                out.write(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));\n                out.close();\n            }catch(Exception ignored){}\n        }\n'''
    j = j.replace(needle, methods, 1)

java.write_text(j, encoding='utf-8')
print('Update data migration patch fixed')
