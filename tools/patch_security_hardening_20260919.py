from pathlib import Path
import re

# Security hardening for production-style WebView APK.
manifest = Path("app/src/main/AndroidManifest.xml")
m = manifest.read_text(encoding="utf-8")
m = m.replace('android:allowBackup="true"', 'android:allowBackup="false"')
m = m.replace('android:usesCleartextTraffic="true"', 'android:usesCleartextTraffic="false"')
manifest.write_text(m, encoding="utf-8")

java = Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
t = java.read_text(encoding="utf-8")

# Harden WebView settings without changing the existing local UI.
t = t.replace(
    's.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setDatabaseEnabled(true); s.setAllowFileAccess(true); s.setAllowContentAccess(true);',
    's.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setDatabaseEnabled(false); s.setAllowFileAccess(true); s.setAllowContentAccess(false); if (Build.VERSION.SDK_INT >= 16) { s.setAllowFileAccessFromFileURLs(false); s.setAllowUniversalAccessFromFileURLs(false); } if (Build.VERSION.SDK_INT >= 26) { s.setSafeBrowsingEnabled(true); }'
)

# Never let an arbitrary external website receive the AndroidBridge.
old = '''@Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r){return handleUrl(r.getUrl().toString());}
            @Override public boolean shouldOverrideUrlLoading(WebView v,String u){return handleUrl(u);}
            @Override public void onPageFinished(WebView v,String u){super.onPageFinished(v,u);migrateStorage(v);injectFeatures();}'''
new = '''@Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r){return handleUrl(r.getUrl().toString());}
            @Override public boolean shouldOverrideUrlLoading(WebView v,String u){return handleUrl(u);}
            @Override public void onPageFinished(WebView v,String u){super.onPageFinished(v,u); if(u != null && u.startsWith("file:///android_asset/")) { migrateStorage(v); injectFeatures(); }}'''
if old in t:
    t = t.replace(old, new)
else:
    # Preserve source if a prior patch changed formatting; fail loudly rather than guessing.
    raise SystemExit("Security patch: WebView lifecycle block not found")

# External web content should open outside the privileged WebView.
old2 = '''private boolean handleUrl(String u){
        if(u.startsWith("tel:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")){try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(u)));}catch(Exception ignored){}return true;} return false;
    }'''
new2 = '''private boolean handleUrl(String u){
        if(u==null) return true;
        if(u.startsWith("tel:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")||u.startsWith("https://")){
            try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(u)));}catch(Exception ignored){}
            return true;
        }
        return !u.startsWith("file:///android_asset/");
    }'''
if old2 in t:
    t = t.replace(old2, new2)
else:
    raise SystemExit("Security patch: URL handler block not found")

java.write_text(t, encoding="utf-8")
print("SECURITY HARDENING OK")
