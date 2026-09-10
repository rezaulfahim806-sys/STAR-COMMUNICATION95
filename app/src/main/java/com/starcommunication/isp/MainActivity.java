package com.starcommunication.isp;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;

public class MainActivity extends Activity {
    private WebView webView;

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
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(190, 190);
        lp.gravity = Gravity.CENTER;
        lp.topMargin = -55;
        splash.addView(logo, lp);

        TextView title = new TextView(this);
        title.setText("STAR COMMUNICATION");
        title.setTextColor(Color.rgb(11,33,69));
        title.setTextSize(22);
        title.setGravity(Gravity.CENTER);
        title.setTypeface(null, android.graphics.Typeface.BOLD);
        FrameLayout.LayoutParams tp = new FrameLayout.LayoutParams(-1, 60);
        tp.gravity = Gravity.CENTER;
        tp.topMargin = 125;
        splash.addView(title, tp);

        TextView sub = new TextView(this);
        sub.setText("ISP MANAGEMENT");
        sub.setTextColor(Color.rgb(22,119,210));
        sub.setTextSize(11);
        sub.setGravity(Gravity.CENTER);
        sub.setTypeface(null, android.graphics.Typeface.BOLD);
        FrameLayout.LayoutParams sp = new FrameLayout.LayoutParams(-1, 40);
        sp.gravity = Gravity.CENTER;
        sp.topMargin = 180;
        splash.addView(sub, sp);

        setContentView(splash);
        splash.postDelayed(() -> openApp(), 1000);
    }

    private void openApp() {
        webView = new WebView(this);
        setContentView(webView);
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        webView.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r){ return handleUrl(r.getUrl().toString()); }
            @Override public boolean shouldOverrideUrlLoading(WebView v, String u){ return handleUrl(u); }
        });
        webView.loadUrl("file:///android_asset/index.html");
    }

    private boolean handleUrl(String u) {
        if (u.startsWith("tel:") || u.startsWith("https://wa.me/") || u.startsWith("whatsapp:")) {
            try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(u))); } catch (Exception ignored) {}
            return true;
        }
        return false;
    }

    @Override public void onBackPressed() {
        if (webView != null) webView.evaluateJavascript("typeof appBack==='function' ? appBack() : null", null);
        else super.onBackPressed();
    }
}