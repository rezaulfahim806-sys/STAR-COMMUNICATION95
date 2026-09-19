from pathlib import Path

manifest = Path("app/src/main/AndroidManifest.xml")
m = manifest.read_text(encoding="utf-8")
m = m.replace('android:allowBackup="true"', 'android:allowBackup="false"')
m = m.replace('android:usesCleartextTraffic="true"', 'android:usesCleartextTraffic="false"')
manifest.write_text(m, encoding="utf-8")

java = Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
t = java.read_text(encoding="utf-8")

old_settings = 's.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setDatabaseEnabled(true); s.setAllowFileAccess(true); s.setAllowContentAccess(true);'
new_settings = 's.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setDatabaseEnabled(false); s.setAllowFileAccess(true); s.setAllowContentAccess(false); if (Build.VERSION.SDK_INT >= 16) { s.setAllowFileAccessFromFileURLs(false); s.setAllowUniversalAccessFromFileURLs(false); } if (Build.VERSION.SDK_INT >= 26) { s.setSafeBrowsingEnabled(true); }'
if old_settings in t:
    t = t.replace(old_settings, new_settings)

# If the hardening is already present, do not fail the build.
if 's.setDatabaseEnabled(false)' not in t or 's.setAllowContentAccess(false)' not in t:
    raise SystemExit("Security patch: hardened WebView settings not found")

lifecycle_new = 'onPageFinished(v,u); if(u != null && u.startsWith("file:///android_asset/")) { migrateStorage(v); injectFeatures(); }'
if lifecycle_new not in t:
    old_lifecycle = 'onPageFinished(v,u);migrateStorage(v);injectFeatures();'
    if old_lifecycle in t:
        t = t.replace(old_lifecycle, lifecycle_new)
    else:
        raise SystemExit("Security patch: WebView lifecycle block not found")

# Replace the old privileged URL handler if present; otherwise accept an already-hardened handler.
old_url = '''private boolean handleUrl(String u){
        if(u.startsWith("tel:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")){try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(u)));}catch(Exception ignored){}return true;} return false;
    }'''
new_url = '''private boolean handleUrl(String u){
        if(u==null) return true;
        if(u.startsWith("tel:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")||u.startsWith("https://")){
            try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(u)));}catch(Exception ignored){}
            return true;
        }
        return !u.startsWith("file:///android_asset/");
    }'''
if old_url in t:
    t = t.replace(old_url, new_url)

if 'u.startsWith("https://")' not in t or 'return !u.startsWith("file:///android_asset/")' not in t:
    raise SystemExit("Security patch: URL handler block not found")

java.write_text(t, encoding="utf-8")
print("SECURITY HARDENING OK")
