package com.starcommunication.isp;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends Activity {
    private WebView webView;
    private static final int SMS_REQ = 501;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        setContentView(webView);
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        webView.addJavascriptInterface(new AppBridge(), "AndroidBridge");
        webView.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r){ return handleUrl(r.getUrl().toString()); }
            @Override public boolean shouldOverrideUrlLoading(WebView v, String u){ return handleUrl(u); }
            private boolean handleUrl(String u){
                if (u.startsWith("tel:") || u.startsWith("https://wa.me/") || u.startsWith("whatsapp:")) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(u))); } catch (Exception ignored) {}
                    return true;
                }
                return false;
            }
            @Override public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                injectFeatures();
            }
        });
        webView.loadUrl("file:///android_asset/index.html");
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.SEND_SMS}, SMS_REQ);
        }
    }

    private void injectFeatures(){
        String js = "javascript:(function(){"+
                "if(window.__starEnhanced)return;window.__starEnhanced=true;"+
                "window.starSms=function(phone,msg){if(window.AndroidBridge){AndroidBridge.sendSms(String(phone),String(msg));}else{location.href='sms:'+phone+'?body='+encodeURIComponent(msg);}};"+
                "window.starBulk=function(mode,msg){try{var a=(window.d&&d.customers)||[];var out=[];a.forEach(function(c){var ok=mode==='all'||(mode==='expired'&&c.status==='expired')||(mode==='unpaid'&&typeof due==='function'&&due(c)>0);if(ok&&c.phone)out.push(c.phone+'|'+(c.name||'Customer'));});if(window.AndroidBridge)AndroidBridge.sendBulk(out.join('\\n'),msg);}catch(e){alert('Message error');}};"+
                "window.starMessageCenter=function(){var h='<h3>💬 Message Center</h3><textarea id=smmsg class=input rows=5 placeholder=Message></textarea><button class=btn full onclick=starBulk(\\'all\\',document.getElementById(\\'smmsg\\').value)>📨 Send to All Customers</button><button class=btn dark full style=margin-top:7px onclick=starBulk(\\'unpaid\\',document.getElementById(\\'smmsg\\').value)>💰 Send to Unpaid Customers</button><button class=btn red full style=margin-top:7px onclick=starBulk(\\'expired\\',document.getElementById(\\'smmsg\\').value)>⏰ Send to Expired Customers</button><div class=muted style=margin-top:8px>Messages are sent by SMS. Make sure SMS permission is allowed.</div>';openSheet(h);};"+
                "var oldDash=window.dashboard;window.dashboard=function(){var h=oldDash();var left=(window.d&&d.customers||[]).filter(function(c){return c.status==='inactive'}).length;var free=(window.d&&d.customers||[]).filter(function(c){return Number(c.fee||0)===0}).length;return h.replace('</div><div class=section><h3>📅 Previous Due</h3>','<div class=stat orange onclick=go(\\'customers\\',{filter:\\'inactive\\'})><div class=label>Total Left Client</div><div class=num>'+left+'</div></div><div class=stat blue onclick=go(\\'customers\\',{filter:\\'all\\'})><div class=label>Free Client</div><div class=num>'+free+'</div></div></div><div class=section><h3>💬 Customer Messages</h3><div class=muted>Send SMS to all, unpaid or expired customers.</div><button class=btn dark full onclick=starMessageCenter()>Open Message Center</button></div><div class=section><h3>📅 Previous Due</h3>');};"+
                "var oldSave=window.saveCustomer;window.saveCustomer=function(){oldSave();try{var c=d.customers[d.customers.length-1];if(c&&c.phone&&c.expiry&&window.AndroidBridge)AndroidBridge.scheduleExpiry(String(c.phone),String(c.name||'Customer'),String(c.expiry));if(c&&c.phone&&window.AndroidBridge)AndroidBridge.scheduleMonthEnd(String(c.phone),String(c.name||'Customer'));}catch(e){}};"+
                "try{(d.customers||[]).forEach(function(c){if(c.phone&&window.AndroidBridge){if(c.expiry)AndroidBridge.scheduleExpiry(String(c.phone),String(c.name||'Customer'),String(c.expiry));AndroidBridge.scheduleMonthEnd(String(c.phone),String(c.name||'Customer'));}});}catch(e){}"+
                "try{render();}catch(e){}"+
                "})();";
        webView.evaluateJavascript(js, null);
    }

    public class AppBridge {
        @JavascriptInterface public void sendSms(String phone, String message){
            if (phone == null || phone.trim().isEmpty() || message == null || message.trim().isEmpty()) return;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "SMS permission required", Toast.LENGTH_SHORT).show());
                return;
            }
            try { android.telephony.SmsManager.getDefault().sendTextMessage(phone, null, message, null, null); }
            catch (Exception e) { runOnUiThread(() -> Toast.makeText(MainActivity.this, "SMS failed", Toast.LENGTH_SHORT).show()); }
        }
        @JavascriptInterface public void sendBulk(String lines, String message){
            if(lines==null||message==null||message.trim().isEmpty())return;
            new Thread(() -> {
                String[] rows=lines.split("\\n");
                for(String row:rows){
                    String[] p=row.split("\\|",2);
                    if(p.length>0&&!p[0].trim().isEmpty()) sendSms(p[0].trim(), message);
                    try{Thread.sleep(700);}catch(Exception ignored){}
                }
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Message sending started", Toast.LENGTH_SHORT).show());
            }).start();
        }
        @JavascriptInterface public void scheduleExpiry(String phone,String name,String expiry){ AutoMessageReceiver.scheduleExpiry(MainActivity.this, phone, name, expiry); }
        @JavascriptInterface public void scheduleMonthEnd(String phone,String name){ AutoMessageReceiver.scheduleMonthEnd(MainActivity.this, phone, name); }
    }

    @Override public void onBackPressed() {
        if (webView != null) webView.evaluateJavascript("typeof appBack==='function' ? appBack() : null", null);
        else super.onBackPressed();
    }
}
