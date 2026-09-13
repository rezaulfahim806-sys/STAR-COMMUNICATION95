from pathlib import Path

ROOT = Path('app/src/main')
manifest = ROOT / 'AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')

if 'android.hardware.telephony.messaging' not in s:
    s = s.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">', '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-feature android:name="android.hardware.telephony" android:required="false" />\n    <uses-feature android:name="android.hardware.telephony.messaging" android:required="false" />')
if 'android.permission.SEND_SMS' not in s:
    s = s.replace('    <uses-permission android:name="android.permission.INTERNET" />', '    <uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="android.permission.SEND_SMS" />')
if 'android.permission.READ_PHONE_STATE' not in s:
    s = s.replace('    <uses-permission android:name="android.permission.SEND_SMS" />', '    <uses-permission android:name="android.permission.SEND_SMS" />\n    <uses-permission android:name="android.permission.READ_PHONE_STATE" />')

components = """
        <activity android:name=".SmsComposeActivity" android:exported="true" android:theme="@style/AppTheme">
            <intent-filter>
                <action android:name="android.intent.action.SENDTO" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:scheme="sms" />
                <data android:scheme="smsto" />
                <data android:scheme="mms" />
                <data android:scheme="mmsto" />
            </intent-filter>
        </activity>
        <service android:name=".SmsRespondService" android:exported="true" android:permission="android.permission.SEND_RESPOND_VIA_MESSAGE">
            <intent-filter>
                <action android:name="android.intent.action.RESPOND_VIA_MESSAGE" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:scheme="sms" />
                <data android:scheme="smsto" />
                <data android:scheme="mms" />
                <data android:scheme="mmsto" />
            </intent-filter>
        </service>
        <receiver android:name=".SmsDeliverReceiver" android:exported="true" android:permission="android.permission.BROADCAST_SMS">
            <intent-filter><action android:name="android.provider.Telephony.SMS_DELIVER" /></intent-filter>
        </receiver>
        <receiver android:name=".MmsDeliverReceiver" android:exported="true" android:permission="android.permission.BROADCAST_WAP_PUSH">
            <intent-filter>
                <action android:name="android.provider.Telephony.WAP_PUSH_DELIVER" />
                <data android:mimeType="application/vnd.wap.mms-message" />
            </intent-filter>
        </receiver>"""
if 'android:name=".SmsComposeActivity"' not in s:
    s = s.replace('        <receiver android:name=".AutoMessageReceiver" android:exported="false" />', components + '\n        <receiver android:name=".AutoMessageReceiver" android:exported="false" />')
manifest.write_text(s, encoding='utf-8')

(ROOT / 'SmsComposeActivity.java').write_text("""package com.starcommunication.isp;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
public class SmsComposeActivity extends Activity {
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent i = new Intent(this, MainActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        Uri data = getIntent() == null ? null : getIntent().getData();
        if (data != null) i.setData(data);
        startActivity(i);
        finish();
    }
}
""", encoding='utf-8')

(ROOT / 'SmsRespondService.java').write_text("""package com.starcommunication.isp;
import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
public class SmsRespondService extends Service {
    @Override public int onStartCommand(Intent intent, int flags, int startId) { stopSelf(startId); return START_NOT_STICKY; }
    @Override public IBinder onBind(Intent intent) { return null; }
}
""", encoding='utf-8')

(ROOT / 'SmsDeliverReceiver.java').write_text("""package com.starcommunication.isp;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
public class SmsDeliverReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) { }
}
""", encoding='utf-8')

(ROOT / 'MmsDeliverReceiver.java').write_text("""package com.starcommunication.isp;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
public class MmsDeliverReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) { }
}
""", encoding='utf-8')

p = ROOT / 'java/com/starcommunication/isp/MainActivity.java'
ms = p.read_text(encoding='utf-8')
if 'import android.app.role.RoleManager;' not in ms:
    ms = ms.replace('import android.app.Activity;', 'import android.app.Activity;\nimport android.app.role.RoleManager;\nimport android.provider.Telephony;')
if 'SMS_ROLE_REQUEST' not in ms:
    ms = ms.replace('private static final int SMS_PERMISSION_REQUEST = 7001;', 'private static final int SMS_PERMISSION_REQUEST = 7001;\n    private static final int SMS_ROLE_REQUEST = 7002;')
ms = ms.replace('        requestSmsPermissions();\n        webView.loadUrl("file:///android_asset/index.html");', '        requestDefaultSmsHandler();\n        webView.loadUrl("file:///android_asset/index.html");')

if 'private void requestDefaultSmsHandler()' not in ms:
    marker = '    private void requestSmsPermission()'
    method = """    private void requestDefaultSmsHandler() {
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                RoleManager rm = (RoleManager) getSystemService(ROLE_SERVICE);
                if (rm != null && rm.isRoleAvailable(RoleManager.ROLE_SMS) && !rm.isRoleHeld(RoleManager.ROLE_SMS)) {
                    startActivityForResult(rm.createRequestRoleIntent(RoleManager.ROLE_SMS), SMS_ROLE_REQUEST);
                    return;
                }
            } else if (Build.VERSION.SDK_INT >= 19) {
                String current = Telephony.Sms.getDefaultSmsPackage(this);
                if (!getPackageName().equals(current)) {
                    Intent i = new Intent(Telephony.Sms.Intents.ACTION_CHANGE_DEFAULT);
                    i.putExtra(Telephony.Sms.Intents.EXTRA_PACKAGE_NAME, getPackageName());
                    startActivityForResult(i, SMS_ROLE_REQUEST);
                    return;
                }
            }
        } catch (Exception ignored) {}
        requestSmsPermissionsIfNeeded();
    }

    private void requestSmsPermissionsIfNeeded() {
        try { requestSmsPermissions(); } catch (Exception ignored) { requestSmsPermission(); }
    }

"""
    ms = ms.replace(marker, method + marker, 1)

if 'private void requestSmsPermissions()' not in ms:
    old = """    private void requestSmsPermission() {
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.SEND_SMS}, SMS_PERMISSION_REQUEST);
        }
    }"""
    new = """    private void requestSmsPermissions() {
        if (Build.VERSION.SDK_INT < 23) return;
        java.util.ArrayList<String> req = new java.util.ArrayList<>();
        if (checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) req.add(Manifest.permission.SEND_SMS);
        if (checkSelfPermission(Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) req.add(Manifest.permission.READ_PHONE_STATE);
        if (!req.isEmpty()) requestPermissions(req.toArray(new String[0]), SMS_PERMISSION_REQUEST);
    }

    private void requestSmsPermission() { requestSmsPermissions(); }"""
    ms = ms.replace(old, new, 1)

needle = '    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {'
if 'onActivityResult(int requestCode' not in ms:
    result = """    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == SMS_ROLE_REQUEST) {
            if (Build.VERSION.SDK_INT >= 29) {
                try {
                    RoleManager rm = (RoleManager) getSystemService(ROLE_SERVICE);
                    if (rm != null && rm.isRoleHeld(RoleManager.ROLE_SMS)) {
                        requestSmsPermissionsIfNeeded();
                        return;
                    }
                } catch (Exception ignored) {}
            } else {
                try {
                    if (getPackageName().equals(Telephony.Sms.getDefaultSmsPackage(this))) {
                        requestSmsPermissionsIfNeeded();
                        return;
                    }
                } catch (Exception ignored) {}
            }
            Toast.makeText(this, "Set STAR COMMUNICATION as Default SMS app to enable direct SIM SMS.", Toast.LENGTH_LONG).show();
        }
    }

"""
    ms = ms.replace(needle, result + needle, 1)

p.write_text(ms, encoding='utf-8')
print('Default SMS handler patch applied.')
