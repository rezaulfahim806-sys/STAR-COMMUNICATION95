package com.starcommunication.isp;

import android.Manifest;
import android.app.*;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.webkit.*;
import android.view.*;

public class MainActivity extends Activity {
    WebView web;
    static final String CHANNEL="bkash";
    @Override public void onCreate(Bundle b){super.onCreate(b); if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED) requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},7); createChannel();
        web=new WebView(this); web.setBackgroundColor(0xfff5f7fb); WebSettings s=web.getSettings(); s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setAllowFileAccess(true); s.setAllowContentAccess(true); s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE); s.setBuiltInZoomControls(false); web.addJavascriptInterface(new Bridge(this),"Android"); web.setWebViewClient(new WebViewClient()); web.loadUrl("file:///android_asset/index.html"); setContentView(web); }
    void createChannel(){ if(Build.VERSION.SDK_INT>=26){ NotificationManager n=(NotificationManager)getSystemService(NOTIFICATION_SERVICE); n.createNotificationChannel(new NotificationChannel(CHANNEL,"bKash Payments",NotificationManager.IMPORTANCE_HIGH)); } }
    @Override public void onBackPressed(){ if(web.canGoBack()) web.goBack(); else super.onBackPressed(); }
    public static class Bridge { Context c; Bridge(Context c){this.c=c;} @JavascriptInterface public void notifyPayment(String title,String body){ NotificationManager n=(NotificationManager)c.getSystemService(Context.NOTIFICATION_SERVICE); Notification.Builder x=Build.VERSION.SDK_INT>=26?new Notification.Builder(c,CHANNEL):new Notification.Builder(c); x.setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(title).setContentText(body).setAutoCancel(true).setPriority(Notification.PRIORITY_HIGH); n.notify((int)System.currentTimeMillis(),x.build()); ((android.os.Vibrator)c.getSystemService(Context.VIBRATOR_SERVICE)).vibrate(300); }}
}
