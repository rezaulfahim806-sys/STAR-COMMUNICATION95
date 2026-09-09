package com.starcommunication.isp;

import android.Manifest;
import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Vibrator;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;

public class MainActivity extends Activity {

    private WebView web;
    private static final String CHANNEL = "bkash";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try {
            createNotificationChannel();

            web = new WebView(this);
            web.setBackgroundColor(0xfff5f7fb);

            WebSettings settings = web.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setDomStorageEnabled(true);
            settings.setAllowFileAccess(true);
            settings.setAllowContentAccess(true);
            settings.setBuiltInZoomControls(false);
            settings.setDisplayZoomControls(false);

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                settings.setMixedContentMode(
                        WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
                );
            }

            web.setWebViewClient(new WebViewClient());

            web.addJavascriptInterface(
                    new Bridge(getApplicationContext()),
                    "Android"
            );

            setContentView(web);

            web.loadUrl("file:///android_asset/index.html");

            if (Build.VERSION.SDK_INT >= 33 &&
                    checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                            != PackageManager.PERMISSION_GRANTED) {

                requestPermissions(
                        new String[]{
                                Manifest.permission.POST_NOTIFICATIONS
                        },
                        7
                );
            }

        } catch (Throwable e) {

            showError(e);
        }
    }

    private void createNotificationChannel() {

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {

            NotificationManager manager =
                    (NotificationManager)
                            getSystemService(NOTIFICATION_SERVICE);

            if (manager != null) {

                NotificationChannel channel =
                        new NotificationChannel(
                                CHANNEL,
                                "bKash Payments",
                                NotificationManager.IMPORTANCE_HIGH
                        );

                manager.createNotificationChannel(channel);
            }
        }
    }

    private void showError(Throwable e) {

        TextView error = new TextView(this);

        error.setText(
                "STAR COMMUNICATION\n\n" +
                "App Error:\n\n" +
                e.getClass().getName() +
                "\n\n" +
                String.valueOf(e.getMessage())
        );

        error.setTextSize(16);
        error.setPadding(40, 80, 40, 40);

        setContentView(error);
    }

    @Override
    public void onBackPressed() {

        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    public static class Bridge {

        private final Context context;

        Bridge(Context context) {
            this.context = context.getApplicationContext();
        }

        @JavascriptInterface
        public void notifyPayment(String title, String body) {

            try {

                NotificationManager manager =
                        (NotificationManager)
                                context.getSystemService(
                                        Context.NOTIFICATION_SERVICE
                                );

                if (manager == null) {
                    return;
                }

                Notification.Builder builder;

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    builder = new Notification.Builder(
                            context,
                            CHANNEL
                    );
                } else {
                    builder = new Notification.Builder(context);
                }

                builder
                        .setSmallIcon(
                                android.R.drawable.ic_dialog_info
                        )
                        .setContentTitle(title)
                        .setContentText(body)
                        .setAutoCancel(true)
                        .setPriority(Notification.PRIORITY_HIGH);

                manager.notify(
                        (int) (System.currentTimeMillis() & 0x7fffffff),
                        builder.build()
                );

                if (Build.VERSION.SDK_INT >= 31 &&
                        context.checkSelfPermission(
                                Manifest.permission.VIBRATE
                        ) != PackageManager.PERMISSION_GRANTED) {
                    return;
                }

                Vibrator vibrator =
                        (Vibrator)
                                context.getSystemService(
                                        Context.VIBRATOR_SERVICE
                                );

                if (vibrator != null && vibrator.hasVibrator()) {

                    if (Build.VERSION.SDK_INT >= 26) {

                        vibrator.vibrate(
                                android.os.VibrationEffect
                                        .createOneShot(
                                                300,
                                                android.os.VibrationEffect
                                                        .DEFAULT_AMPLITUDE
                                        )
                        );

                    } else {
                        vibrator.vibrate(300);
                    }
                }

            } catch (Throwable ignored) {
                // Notification/vibration failure
                // must never crash the application.
            }
        }
    }
}
