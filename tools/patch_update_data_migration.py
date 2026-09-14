from pathlib import Path

# Preserve data across app updates by migrating legacy WebView keys and native backup.
html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

# Replace the startup data-loading statement with a migration-aware loader.
old = "let d;try{let native='';try{native=window.AndroidBridge&&AndroidBridge.loadData?AndroidBridge.loadData():''}catch(e){}d=JSON.parse(native||localStorage.getItem(KEY)||localStorage.getItem(KEY+'_backup')||'null')}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));"
new = "let d;try{let raw='';try{raw=window.AndroidBridge&&AndroidBridge.loadData?AndroidBridge.loadData():''}catch(e){}let keys=[KEY,'star_communication_final_v2','star_communication_final_v1','star_communication'];if(!raw){for(let k of keys){try{raw=localStorage.getItem(k)||localStorage.getItem(k+'_backup')||''}catch(e){}if(raw)break}}d=raw?JSON.parse(raw):null}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));"
if old in s:
    s = s.replace(old, new, 1)

# Ensure saves write the current key, legacy-compatible backup, and native storage.
old_save = "function save(){let z=JSON.stringify(d);localStorage.setItem(KEY,z);try{localStorage.setItem(KEY+'_backup',z)}catch(e){}try{if(window.AndroidBridge&&AndroidBridge.saveData)AndroidBridge.saveData(z)}catch(e){}}"
new_save = "function save(){let z=JSON.stringify(d);try{localStorage.setItem(KEY,z);localStorage.setItem(KEY+'_backup',z)}catch(e){}try{if(window.AndroidBridge&&AndroidBridge.saveData)AndroidBridge.saveData(z)}catch(e){}}"
if old_save in s:
    s = s.replace(old_save, new_save, 1)

# After successful migration, immediately persist it in the new storage format.
marker = "if(!d)d=JSON.parse(JSON.stringify(DEF));"
if marker in s and "__starDataMigrated" not in s:
    s = s.replace(marker, marker+"try{window.__starDataMigrated=true;if(d&&d.customers)save()}catch(e){}", 1)

html.write_text(s, encoding='utf-8')

java = Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
j = java.read_text(encoding='utf-8')

imports = 'import java.io.File;\nimport java.io.FileInputStream;\nimport java.io.FileOutputStream;\n'
if 'import java.io.File;' not in j:
    j = j.replace('import android.widget.Toast;\n', 'import android.widget.Toast;\n'+imports, 1)
else:
    if 'import java.io.FileInputStream;' not in j:
        j = j.replace('import java.io.File;\n', imports, 1)

needle = '    public class AppBridge {\n'
if 'star_customer_data.json' not in j:
    methods = '''    public class AppBridge {\n        @JavascriptInterface public String loadData(){\n            try{\n                File f=new File(getFilesDir(),"star_customer_data.json");\n                if(!f.exists())return "";\n                FileInputStream in=new FileInputStream(f);\n                byte[] b=new byte[(int)f.length()];\n                int n=in.read(b); in.close();\n                return n>0?new String(b,java.nio.charset.StandardCharsets.UTF_8):"";\n            }catch(Exception e){return "";}\n        }\n        @JavascriptInterface public void saveData(String json){\n            if(json==null||json.isEmpty())return;\n            try{\n                File f=new File(getFilesDir(),"star_customer_data.json");\n                FileOutputStream out=new FileOutputStream(f);\n                out.write(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));\n                out.close();\n            }catch(Exception ignored){}\n        }\n'''
    if needle not in j:
        raise SystemExit('AppBridge class not found')
    j = j.replace(needle, methods, 1)

java.write_text(j, encoding='utf-8')
print('Update data migration applied')
