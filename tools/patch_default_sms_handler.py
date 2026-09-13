from pathlib import Path

ROOT = Path('app/src/main')
manifest = ROOT / 'AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')
if 'android.hardware.telephony.messaging' not in s:
    s = s.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">', '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-feature android:name="android.hardware.telephony" android:required="false" />\n    <uses-feature android:name="android.hardware.telephony.messaging" android:required="false" />')
if 'android.permission.READ_PHONE_STATE' not in s:
    s = s.replace('    <uses-permission android:name="android.permission.SEND_SMS" />', '    <uses-permission android:name="android.permission.SEND_SMS" />\n    <uses-permission android:name="android.permission.READ_PHONE_STATE" />')
components = '''        <activity android:name=".SmsComposeActivity" android:exported="true" android:theme="@style/AppTheme"><intent-filter><action android:name="android.intent.action.SENDTO" /><category android:name="android.intent.category.DEFAULT" /><data android:scheme="sms" /><data android:scheme="smsto" /><data android:scheme="mms" /><data android:scheme="mmsto" /></intent-filter></activity>\n        <service android:name=".SmsRespondService" android:exported="true" android:permission="android.permission.SEND_RESPOND_VIA_MESSAGE"><intent-filter><action android:name="android.intent.action.RESPOND_VIA_MESSAGE" /><category android:name="android.intent.category.DEFAULT" /><data android:scheme="sms" /><data android:scheme="smsto" /><data android:scheme="mms" /><data android:scheme="mmsto" /></intent-filter></service>\n        <receiver android:name=".SmsDeliverReceiver" android:exported="true" android:permission="android.permission.BROADCAST_SMS"><intent-filter><action android:name="android.provider.Telephony.SMS_DELIVER" /></intent-filter></receiver>\n        <receiver android:name=".MmsDeliverReceiver" android:exported="true" android:permission="android.permission.BROADCAST_WAP_PUSH"><intent-filter><action android:name="android.provider.Telephony.WAP_PUSH_DELIVER" /><data android:mimeType="application/vnd.wap.mms-message" /></intent-filter></receiver>'''
if 'android:name=".SmsComposeActivity"' not in s:
    s = s.replace('        <receiver android:name=".AutoMessageReceiver" android:exported="false" />', components + '\n        <receiver android:name=".AutoMessageReceiver" android:exported="false" />')
manifest.write_text(s, encoding='utf-8')
(ROOT/'SmsComposeActivity.java').write_text('''package com.starcommunication.isp;\nimport android.app.Activity;\nimport android.content.Intent;\nimport android.os.Bundle;\npublic class SmsComposeActivity extends Activity {\n @Override protected void onCreate(Bundle b){super.onCreate(b); Intent i=new Intent(this,MainActivity.class); i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP); startActivity(i); finish();}\n}\n''', encoding='utf-8')
(ROOT/'SmsRespondService.java').write_text('''package com.starcommunication.isp;\nimport android.app.Service;\nimport android.content.Intent;\nimport android.os.IBinder;\npublic class SmsRespondService extends Service {\n @Override public int onStartCommand(Intent i,int f,int id){stopSelf(id);return START_NOT_STICKY;}\n @Override public IBinder onBind(Intent i){return null;}\n}\n''', encoding='utf-8')
(ROOT/'SmsDeliverReceiver.java').write_text('''package com.starcommunication.isp;\nimport android.content.BroadcastReceiver;\nimport android.content.Context;\nimport android.content.Intent;\npublic class SmsDeliverReceiver extends BroadcastReceiver { @Override public void onReceive(Context c,Intent i){} }\n''', encoding='utf-8')
(ROOT/'MmsDeliverReceiver.java').write_text('''package com.starcommunication.isp;\nimport android.content.BroadcastReceiver;\nimport android.content.Context;\nimport android.content.Intent;\npublic class MmsDeliverReceiver extends BroadcastReceiver { @Override public void onReceive(Context c,Intent i){} }\n''', encoding='utf-8')

p=ROOT/'java/com/starcommunication/isp/MainActivity.java'
ms=p.read_text(encoding='utf-8')
if 'import android.app.role.RoleManager;' not in ms:
    ms=ms.replace('import android.app.Activity;','import android.app.Activity;\nimport android.app.role.RoleManager;\nimport android.provider.Telephony;')
if 'SMS_ROLE_REQUEST' not in ms:
    ms=ms.replace('private static final int SMS_PERMISSION_REQUEST = 7001;','private static final int SMS_PERMISSION_REQUEST = 7001;\n    private static final int SMS_ROLE_REQUEST = 7002;')
if 'private void requestDefaultSmsHandler()' not in ms:
    marker='    private void requestSmsPermission()'
    method='''    private void requestDefaultSmsHandler(){\n        try{\n            if(Build.VERSION.SDK_INT>=29){RoleManager rm=(RoleManager)getSystemService(ROLE_SERVICE); if(rm!=null&&rm.isRoleAvailable(RoleManager.ROLE_SMS)&&!rm.isRoleHeld(RoleManager.ROLE_SMS)){startActivityForResult(rm.createRequestRoleIntent(RoleManager.ROLE_SMS),SMS_ROLE_REQUEST);return;}}\n            else if(Build.VERSION.SDK_INT>=19){String cur=Telephony.Sms.getDefaultSmsPackage(this); if(!getPackageName().equals(cur)){Intent i=new Intent(Telephony.Sms.Intents.ACTION_CHANGE_DEFAULT); i.putExtra(Telephony.Sms.Intents.EXTRA_PACKAGE_NAME,getPackageName()); startActivityForResult(i,SMS_ROLE_REQUEST);return;}}\n        }catch(Exception ignored){}\n        requestSmsPermissions();\n    }\n\n'''
    ms=ms.replace(marker,method+marker,1)
# Do not inject a second requestSmsPermissions method if another patch already added it.
if 'private void requestSmsPermissions()' not in ms:
    marker='    private void requestSmsPermission()'
    method='''    private void requestSmsPermissions(){\n        if(Build.VERSION.SDK_INT<23)return;\n        java.util.ArrayList<String> req=new java.util.ArrayList<>();\n        if(checkSelfPermission(Manifest.permission.SEND_SMS)!=PackageManager.PERMISSION_GRANTED)req.add(Manifest.permission.SEND_SMS);\n        if(checkSelfPermission(Manifest.permission.READ_PHONE_STATE)!=PackageManager.PERMISSION_GRANTED)req.add(Manifest.permission.READ_PHONE_STATE);\n        if(!req.isEmpty())requestPermissions(req.toArray(new String[0]),SMS_PERMISSION_REQUEST);\n    }\n\n'''
    ms=ms.replace(marker,method+marker,1)
old='''    private void requestSmsPermission() {\n        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {\n            requestPermissions(new String[]{Manifest.permission.SEND_SMS}, SMS_PERMISSION_REQUEST);\n        }\n    }'''
if old in ms: ms=ms.replace(old,'    private void requestSmsPermission() { requestSmsPermissions(); }',1)
if 'onActivityResult(int requestCode' not in ms:
    needle='    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {'
    result='''    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){\n        super.onActivityResult(requestCode,resultCode,data);\n        if(requestCode==SMS_ROLE_REQUEST){\n            boolean held=false;\n            try{if(Build.VERSION.SDK_INT>=29){RoleManager rm=(RoleManager)getSystemService(ROLE_SERVICE);held=rm!=null&&rm.isRoleHeld(RoleManager.ROLE_SMS);}else if(Build.VERSION.SDK_INT>=19){held=getPackageName().equals(Telephony.Sms.getDefaultSmsPackage(this));}}catch(Exception ignored){}\n            if(held)requestSmsPermissions(); else Toast.makeText(this,"Direct SIM SMS needs STAR COMMUNICATION as the Default SMS app.",Toast.LENGTH_LONG).show();\n        }\n    }\n\n'''
    ms=ms.replace(needle,result+needle,1)
if 'requestDefaultSmsHandler();\n        webView.loadUrl' not in ms:
    ms=ms.replace('        webView.loadUrl("file:///android_asset/index.html");','        requestDefaultSmsHandler();\n        webView.loadUrl("file:///android_asset/index.html");',1)
p.write_text(ms,encoding='utf-8')
print('Default SMS handler patch applied successfully; duplicate permission method prevented.')
