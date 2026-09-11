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
import android.telephony.SubscriptionInfo;
import android.telephony.SubscriptionManager;
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
import java.util.List;

public class MainActivity extends Activity {
    private WebView webView;
    private static final int SMS_PERMISSION_REQUEST = 7001;
    private static final int PHONE_STATE_PERMISSION_REQUEST = 7002;

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

    private boolean hasPhoneStatePermission() {
        return Build.VERSION.SDK_INT < 23 || checkSelfPermission(Manifest.permission.READ_PHONE_STATE) == PackageManager.PERMISSION_GRANTED;
    }

    private void requestPhoneStatePermission() {
        if (Build.VERSION.SDK_INT >= 23 && !hasPhoneStatePermission()) {
            requestPermissions(new String[]{Manifest.permission.READ_PHONE_STATE}, PHONE_STATE_PERMISSION_REQUEST);
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
        } else if (requestCode == PHONE_STATE_PERMISSION_REQUEST) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "SIM 2 access enabled", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "SIM 2 access denied. SMS cannot be forced to SIM 2.", Toast.LENGTH_LONG).show();
            }
        }
    }

    private SmsManager getSim2SmsManager() {
        if (Build.VERSION.SDK_INT < 22) return SmsManager.getDefault();
        if (!hasPhoneStatePermission()) {
            requestPhoneStatePermission();
            return null;
        }
        try {
            SubscriptionManager sm = (SubscriptionManager) getSystemService(TELEPHONY_SUBSCRIPTION_SERVICE);
            if (sm == null) return null;
            SubscriptionInfo sim2 = sm.getActiveSubscriptionInfoForSimSlotIndex(1);
            if (sim2 == null) return null;
            if (Build.VERSION.SDK_INT >= 22) return SmsManager.getSmsManagerForSubscriptionId(sim2.getSubscriptionId());
        } catch (SecurityException e) {
            requestPhoneStatePermission();
        } catch (Exception ignored) {}
        return null;
    }

    private void injectFeatures(){
        String js="javascript:(function(){"+
        "if(window.__starEnhanced)return;window.__starEnhanced=true;"+
        "window.starBulk=function(mode,msg){try{if(!msg||!msg.trim()){toast('Write a message first');return;}var a=(window.d&&d.customers)||[],out=[];a.forEach(function(c){var ok=mode==='all'||(mode==='expired'&&c.status==='expired')||(mode==='unpaid'&&typeof due==='function'&&due(c)>0);if(ok&&c.phone)out.push(c.phone+'|'+(c.name||'Customer'));});if(window.AndroidBridge)AndroidBridge.sendBulk(out.join('\\n'),msg);}catch(e){toast('Message error');}};"+
        "window.starMessageCenter=function(){openSheet('<h3>💬 Message Center</h3><textarea id=smmsg class=input rows=5 placeholder=Message></textarea><button class=btn full onclick=starBulk(\\'all\\',smmsg.value)>📨 Send to All Customers</button><button class=btn dark full style=margin-top:7px onclick=starBulk(\\'unpaid\\',smmsg.value)>💰 Send to Unpaid</button><button class=btn red full style=margin-top:7px onclick=starBulk(\\'expired\\',smmsg.value)>⏰ Send to Expired</button><div class=muted style=margin-top:8px>Direct SIM SMS uses SIM 2 and deducts its carrier SMS balance.</div>');};"+
        "window.dashboard=function(){fix();var a=d.customers||[],left=a.filter(function(c){return c.status==='inactive'}).length,free=a.filter(function(c){return Number(c.fee||0)===0}).length,paidMoney=totalPaid(),unpaidMoney=totalUnpaid(),cur=month(),active=a.filter(function(c){return c.status==='active'||c.status==='inactive'}),monthlyBill=active.reduce(function(s,c){return s+Number(c.fee||0)},0),newc=a.filter(function(c){return String(c.createdAt||c.connectionDate||'').slice(0,7)===cur}),newbill=newc.reduce(function(s,c){return s+Number(c.fee||0)},0),nextc=a.filter(function(c){return c.status!=='expired'}),nextbill=nextc.reduce(function(s,c){return s+Number(c.fee||0)},0),g=newGrowth(),m=Number(cur.slice(5,7))-1;return '<h1 class=\"title\">Dashboard</h1><div class=\"sub\">'+cur+' • Billing cycle: 1–31</div><div class=\"grid\"><div class=\"stat orange\" onclick=\"go(\\\'customers\\\',{filter:\\\'inactive\\\'})\"><div class=\"label\">Total Left Client</div><div class=\"num\">'+left+'</div></div><div class=\"stat blue\" onclick=\"go(\\\'customers\\\',{filter:\\\'all\\\'})\"><div class=\"label\">Free Client</div><div class=\"num\">'+free+'</div></div></div><div class=\"grid\"><div class=\"stat purple\" onclick=\"go(\\\'customers\\\',{filter:\\\'paid\\\'})\"><div class=\"label\">Total Paid</div><div class=\"num\">'+money(paidMoney)+'</div></div><div class=\"stat red\" onclick=\"go(\\\'customers\\\',{filter:\\\'unpaid\\\'})\"><div class=\"label\">Total Unpaid</div><div class=\"num\">'+money(unpaidMoney)+'</div></div></div><div class=\"section\"><h3>📊 Monthly Customer & Bill</h3><div class=\"kpi\"><span>This Month Customers</span><b>'+active.length+'</b></div><div class=\"kpi\"><span>This Month Expected Bill</span><b>'+money(monthlyBill)+'</b></div><div class=\"kpi\"><span>New Connections This Month</span><b>'+newc.length+'</b></div><div class=\"kpi\"><span>New Connection Bill</span><b>'+money(newbill)+'</b></div><div class=\"kpi\"><span>Next Month Customers</span><b>'+nextc.length+'</b></div><div class=\"kpi\"><span>Next Month Projected Bill</span><b>'+money(nextbill)+'</b></div></div><div class=\"chart\"><b>📈 Monthly New Connection Growth</b>'+bars(g,'greenbar')+'</div>';};"+
        "try{render();}catch(e){}})();";
        webView.evaluateJavascript(js,null);
    }

    public class AppBridge {
        @JavascriptInterface public void sendSms(String phone,String message){
            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty())return;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(() -> { Toast.makeText(MainActivity.this,"SMS permission is required for SIM SMS.",Toast.LENGTH_LONG).show(); requestSmsPermission(); });
                return;
            }
            SmsManager sms = getSim2SmsManager();
            if (sms == null) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this,"SIM 2 is not available. Insert 01897-099850 in SIM 2 and allow phone/SMS permission.",Toast.LENGTH_LONG).show());
                return;
            }
            try{
                sms.sendTextMessage(phone.trim(),null,message,null,null);
                runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS sent using SIM 2 balance",Toast.LENGTH_SHORT).show());
            }catch(SecurityException e){runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS permission denied by Android",Toast.LENGTH_LONG).show());}
            catch(Exception e){runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS failed: check SIM 2/network/balance",Toast.LENGTH_LONG).show());}
        }
        @JavascriptInterface public void sendBulk(String lines,String message){
            if(lines==null||message==null||message.trim().isEmpty())return;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(this::requestSmsPermission);
                return;
            }
            SmsManager sms = getSim2SmsManager();
            if (sms == null) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this,"SIM 2 is not available. Insert 01897-099850 in SIM 2 and allow phone/SMS permission.",Toast.LENGTH_LONG).show());
                return;
            }
            String[] rows=lines.split("\\n");
            int sent=0;
            for(String row:rows){
                try{String[] p=row.split("\\|",2);if(p.length>0&&!p[0].trim().isEmpty()){sms.sendTextMessage(p[0].trim(),null,message,null,null);sent++;}Thread.sleep(250);}catch(Exception ignored){}
            }
            final int count=sent;
            runOnUiThread(()->Toast.makeText(MainActivity.this,"SIM 2 SMS send started: "+count+" messages",Toast.LENGTH_LONG).show());
        }
        @JavascriptInterface public void scheduleExpiry(String phone,String name,String expiry){AutoMessageReceiver.scheduleExpiry(MainActivity.this,phone,name,expiry);}
        @JavascriptInterface public void scheduleMonthEnd(String phone,String name){AutoMessageReceiver.scheduleMonthEnd(MainActivity.this,phone,name);}
        private void requestSmsPermission(){MainActivity.this.requestSmsPermission();}
    }

    @Override public void onBackPressed(){if(webView!=null)webView.evaluateJavascript("typeof appBack==='function' ? appBack() : null",null);else super.onBackPressed();}
}
