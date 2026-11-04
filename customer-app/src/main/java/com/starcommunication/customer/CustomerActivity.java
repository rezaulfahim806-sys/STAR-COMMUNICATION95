package com.starcommunication.customer;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class CustomerActivity extends Activity {
  private WebView web;
  private static final String REMOTE_HTML = "https://raw.githubusercontent.com/rezaulfahim806-sys/STAR-COMMUNICATION95/customer-apk-bangla-blue/customer-app/src/main/assets/customer.html";
  @Override public void onCreate(Bundle b){ super.onCreate(b); web=new WebView(this); setContentView(web); WebSettings s=web.getSettings(); s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setAllowFileAccess(false); s.setAllowContentAccess(false); web.setBackgroundColor(Color.WHITE); web.setWebViewClient(new WebViewClient()); loadFreshPage(); }
  private void loadFreshPage(){ new Thread(()->{String html=null; HttpURLConnection c=null; try{ c=(HttpURLConnection)new URL(REMOTE_HTML).openConnection(); c.setConnectTimeout(5000); c.setReadTimeout(5000); c.setUseCaches(false); c.setRequestProperty("Cache-Control","no-cache"); if(c.getResponseCode()==200){try(InputStream in=c.getInputStream(); ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] buf=new byte[8192];int n;while((n=in.read(buf))>0&&out.size()<2*1024*1024)out.write(buf,0,n);String x=out.toString("UTF-8");if(x.contains("STAR COMMUNICATION")&&x.contains("<html"))html=x;}}}catch(Exception ignored){}finally{if(c!=null)c.disconnect();} final String page=html; runOnUiThread(()->{if(page!=null)web.loadDataWithBaseURL("https://raw.githubusercontent.com/rezaulfahim806-sys/STAR-COMMUNICATION95/customer-apk-bangla-blue/customer-app/src/main/assets/",page,"text/html","UTF-8",null);else web.loadUrl("file:///android_asset/customer.html");}); }).start(); }
  @Override public void onBackPressed(){if(web!=null&&web.canGoBack())web.goBack();else super.onBackPressed();}
}
