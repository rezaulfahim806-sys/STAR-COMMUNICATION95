package com.starcommunication.isp;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.telephony.SmsManager;
import android.view.Gravity;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private WebView webView;
    private static final int SMS_PERMISSION_REQUEST = 7001;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showSplash();
    }

    private void showSplash() {
        FrameLayout splash = new FrameLayout(this);
        splash.setBackgroundColor(Color.WHITE);
        ImageView logo = new ImageView(this);
        logo.setImageResource(com.starcommunication.isp.R.drawable.star_splash_logo);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(190,190);
        lp.gravity = Gravity.CENTER; lp.topMargin = -55; splash.addView(logo,lp);
        TextView title = new TextView(this);
        title.setText("STAR COMMUNICATION"); title.setTextColor(Color.rgb(11,33,69)); title.setTextSize(22); title.setGravity(Gravity.CENTER); title.setTypeface(null,android.graphics.Typeface.BOLD);
        FrameLayout.LayoutParams tp = new FrameLayout.LayoutParams(-1,60); tp.gravity=Gravity.CENTER; tp.topMargin=125; splash.addView(title,tp);
        TextView sub = new TextView(this);
        sub.setText("ISP MANAGEMENT"); sub.setTextColor(Color.rgb(22,119,210)); sub.setTextSize(11); sub.setGravity(Gravity.CENTER); sub.setTypeface(null,android.graphics.Typeface.BOLD);
        FrameLayout.LayoutParams sp = new FrameLayout.LayoutParams(-1,40); sp.gravity=Gravity.CENTER; sp.topMargin=180; splash.addView(sub,sp);
        setContentView(splash);
        splash.postDelayed(this::openApp,1000);
    }

    private void openApp() {
        webView = new WebView(this); setContentView(webView);
        WebSettings s=webView.getSettings(); s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setDatabaseEnabled(true); s.setAllowFileAccess(true); s.setAllowContentAccess(true);
        webView.addJavascriptInterface(new AppBridge(),"AndroidBridge");
        webView.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r){return handleUrl(r.getUrl().toString());}
            @Override public boolean shouldOverrideUrlLoading(WebView v,String u){return handleUrl(u);}
            @Override public void onPageFinished(WebView v,String u){super.onPageFinished(v,u);injectFeatures();}
        });
        webView.loadUrl("file:///android_asset/index.html");
    }

    private boolean handleUrl(String u){
        if(u.startsWith("tel:")||u.startsWith("https://wa.me/")||u.startsWith("whatsapp:")){try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(u)));}catch(Exception ignored){}return true;} return false;
    }

    private void requestSmsPermission() {
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.SEND_SMS}, SMS_PERMISSION_REQUEST);
        }
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == SMS_PERMISSION_REQUEST) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "SIM SMS permission enabled", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "SMS permission denied. Direct SIM SMS cannot work.", Toast.LENGTH_LONG).show();
            }
        }
    }

    private void injectFeatures(){
        String js="javascript:(function(){"+
        "if(window.__starEnhanced)return;window.__starEnhanced=true;"+
        "window.starBulk=function(mode,msg){try{if(!msg||!msg.trim()){toast('Write a message first');return;}var a=(window.d&&d.customers)||[],out=[];a.forEach(function(c){var ok=mode==='all'||(mode==='expired'&&c.status==='expired')||(mode==='unpaid'&&typeof due==='function'&&due(c)>0);if(ok&&c.phone)out.push(c.phone+'|'+(c.name||'Customer'));});if(window.AndroidBridge)AndroidBridge.sendBulk(out.join('\\n'),msg);}catch(e){toast('Message error');}};"+
        "window.starMessageCenter=function(){openSheet('<h3>💬 Message Center</h3><textarea id=smmsg class=input rows=5 placeholder=Message></textarea><button class=btn full onclick=starBulk(\\'all\\',smmsg.value)>📨 Send to All Customers</button><button class=btn dark full style=margin-top:7px onclick=starBulk(\\'unpaid\\',smmsg.value)>💰 Send to Unpaid</button><button class=btn red full style=margin-top:7px onclick=starBulk(\\'expired\\',smmsg.value)>⏰ Send to Expired</button><div class=muted style=margin-top:8px>Direct SIM SMS uses the phone SIM and deducts carrier SMS balance.</div>');};"+
        "function starMonthlySummary(){var a=(d.customers||[]),cur=(typeof month==='function'?month():'').toString(),active=a.filter(function(c){return c.status==='active'||c.status==='inactive'}),bill=active.reduce(function(s,c){return s+Number(c.fee||0)},0),newc=a.filter(function(c){return String(c.createdAt||c.connectionDate||'').slice(0,7)===cur}),newbill=newc.reduce(function(s,c){return s+Number(c.fee||0)},0),nextc=a.filter(function(c){return c.status!=='expired'}),nextbill=nextc.reduce(function(s,c){return s+Number(c.fee||0)},0),free=a.filter(function(c){return Number(c.fee||0)===0}).length;return '<div class=section><h3>📊 Monthly Customer & Bill</h3><div class=kpi><span>This Month Customers</span><b>'+active.length+'</b></div><div class=kpi><span>This Month Expected Bill</span><b>'+money(bill)+'</b></div><div class=kpi><span>New Customers This Month</span><b>'+newc.length+'</b></div><div class=kpi><span>New Customer Bill</span><b>'+money(newbill)+'</b></div><div class=kpi><span>Next Month Projected Customers</span><b>'+nextc.length+'</b></div><div class=kpi><span>Next Month Projected Bill</span><b>'+money(nextbill)+'</b></div><div class=kpi><span>Free Client</span><b>'+free+'</b></div></div>';};"+
        "var oldDash=window.dashboard;window.dashboard=function(){var h=oldDash(),left=(d.customers||[]).filter(function(c){return c.status==='inactive'}).length,free=(d.customers||[]).filter(function(c){return Number(c.fee||0)===0}).length;var marker='<h1 class=\"title\">Dashboard</h1>';var add='<div class=grid><div class=stat style=\"background:#ed7d16;color:#fff\" onclick=\"go(\\\'customers\\\',{filter:\\\'inactive\\\'})\"><div class=label>Total Left Client</div><div class=num>'+left+'</div></div><div class=stat style=\"background:#1677d2;color:#fff\" onclick=\"go(\\\'customers\\\',{filter:\\\'all\\\'})\"><div class=label>Free Client</div><div class=num>'+free+'</div></div></div>'+starMonthlySummary()+'<div class=section><h3>📦 Package</h3><div class=kpi><span>Available Packages</span><b>20 Mb • 30 Mb • 40 Mb • 50 Mb</b></div></div><div class=section><h3>💬 Customer Messages</h3><div class=muted>Send direct SIM SMS to all, unpaid or expired customers.</div><button class=btn dark full onclick=starMessageCenter()>Open Message Center</button></div>';return h.replace(marker,marker+add);};"+
        "var oldAdd=window.addCustomer;window.addCustomer=function(){openSheet('<h3>Add Customer</h3><input id=n class=input placeholder=Customer name><input id=p class=input placeholder=Mobile / WhatsApp><input id=a class=input placeholder=Address><label class=muted>Package</label><select id=pkg class=select><option value=20 Mb>20 Mb</option><option value=30 Mb>30 Mb</option><option value=40 Mb>40 Mb</option><option value=50 Mb>50 Mb</option></select><input id=fee class=input type=number placeholder=Monthly fee><input id=pp class=input placeholder=PPPoE username><input id=pw class=input placeholder=PPPoE password><input id=onu class=input placeholder=ONU ID><label class=muted>Connection Date</label><input id=cd class=input type=date value='+today()+'><label class=muted>Expiry Date</label><input id=ex class=input type=date><input id=prev class=input type=number value=0 placeholder=Previous due><select id=st class=select><option value=active>Active</option><option value=inactive>Inactive</option></select><button class=btn green full onclick=saveCustomer()>Save Customer</button>');};"+
        "var oldSave=window.saveCustomer;window.saveCustomer=function(){oldSave();try{var c=d.customers[d.customers.length-1];if(c&&c.phone&&c.expiry)AndroidBridge.scheduleExpiry(String(c.phone),String(c.name||'Customer'),String(c.expiry));if(c&&c.phone)AndroidBridge.scheduleMonthEnd(String(c.phone),String(c.name||'Customer'));}catch(e){}};"+
        "try{(d.customers||[]).forEach(function(c){if(c.phone){if(c.expiry)AndroidBridge.scheduleExpiry(String(c.phone),String(c.name||'Customer'),String(c.expiry));AndroidBridge.scheduleMonthEnd(String(c.phone),String(c.name||'Customer'));}});}catch(e){}try{render();}catch(e){}})();";
        webView.evaluateJavascript(js,null);
    }

    public class AppBridge {
        @JavascriptInterface public void sendSms(String phone,String message){
            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty())return;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(() -> { Toast.makeText(MainActivity.this,"SMS permission is required for SIM SMS.",Toast.LENGTH_LONG).show(); requestSmsPermission(); });
                return;
            }
            try{
                SmsManager sms = SmsManager.getDefault();
                sms.sendTextMessage(phone.trim(),null,message,null,null);
                runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS sent using SIM balance",Toast.LENGTH_SHORT).show());
            }catch(SecurityException e){runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS permission denied by Android",Toast.LENGTH_LONG).show());}
            catch(Exception e){runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS failed: check SIM/network/balance",Toast.LENGTH_LONG).show());}
        }
        @JavascriptInterface public void sendBulk(String lines,String message){
            if(lines==null||message==null||message.trim().isEmpty())return;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(this::requestSmsPermission);
                return;
            }
            String[] rows=lines.split("\\n");
            int sent=0;
            for(String row:rows){
                try{String[] p=row.split("\\|",2);if(p.length>0&&!p[0].trim().isEmpty()){SmsManager.getDefault().sendTextMessage(p[0].trim(),null,message,null,null);sent++;}Thread.sleep(250);}catch(Exception ignored){}
            }
            final int count=sent;
            runOnUiThread(()->Toast.makeText(MainActivity.this,"SIM SMS send started: "+count+" messages",Toast.LENGTH_LONG).show());
        }
        @JavascriptInterface public void scheduleExpiry(String phone,String name,String expiry){AutoMessageReceiver.scheduleExpiry(MainActivity.this,phone,name,expiry);}
        @JavascriptInterface public void scheduleMonthEnd(String phone,String name){AutoMessageReceiver.scheduleMonthEnd(MainActivity.this,phone,name);}
        private void requestSmsPermission(){MainActivity.this.requestSmsPermission();}
    }

    @Override public void onBackPressed(){if(webView!=null)webView.evaluateJavascript("typeof appBack==='function' ? appBack() : null",null);else super.onBackPressed();}
}
