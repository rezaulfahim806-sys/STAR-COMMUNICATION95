package com.starcommunication.isp;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;

public class MainActivity extends Activity {
    private WebView webView;
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
        webView.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r){
                String u = r.getUrl().toString();
                if (u.startsWith("tel:") || u.startsWith("https://wa.me/") || u.startsWith("whatsapp:")) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(u))); } catch (Exception ignored) {}
                    return true;
                }
                return false;
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v, String u){
                if (u.startsWith("tel:") || u.startsWith("https://wa.me/") || u.startsWith("whatsapp:")) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(u))); } catch (Exception ignored) {}
                    return true;
                }
                return false;
            }
        });
        webView.loadUrl("file:///android_asset/index.html");
    }
    @Override public void onBackPressed() {
        if (webView != null) webView.evaluateJavascript("typeof appBack==='function' ? appBack() : null", null);
        else super.onBackPressed();
    }
}