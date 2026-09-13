from pathlib import Path

# Fix direct SIM SMS permission + SIM 2 (Robi) selection.
manifest = Path('app/src/main/AndroidManifest.xml')
s = manifest.read_text(encoding='utf-8')
if 'android.permission.READ_PHONE_STATE' not in s:
    s = s.replace('    <uses-permission android:name="android.permission.SEND_SMS" />', '    <uses-permission android:name="android.permission.SEND_SMS" />\n    <uses-permission android:name="android.permission.READ_PHONE_STATE" />')
manifest.write_text(s, encoding='utf-8')

p = Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
s = p.read_text(encoding='utf-8')

# Request both permissions when the app opens. This prevents the SMS feature from
# silently failing after a fresh install/update.
s = s.replace('        webView.loadUrl("file:///android_asset/index.html");', '        requestSmsPermissions();\n        webView.loadUrl("file:///android_asset/index.html");')

# Replace the old single-permission helper with a combined helper.
old = '''    private void requestSmsPermission() {\n        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {\n            requestPermissions(new String[]{Manifest.permission.SEND_SMS}, SMS_PERMISSION_REQUEST);\n        }\n    }'''
new = '''    private void requestSmsPermissions() {\n        if (Build.VERSION.SDK_INT < 23) return;\n        java.util.ArrayList<String> req = new java.util.ArrayList<>();\n        if (checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) req.add(Manifest.permission.SEND_SMS);\n        if (checkSelfPermission(Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) req.add(Manifest.permission.READ_PHONE_STATE);\n        if (!req.isEmpty()) requestPermissions(req.toArray(new String[0]), SMS_PERMISSION_REQUEST);\n    }\n\n    private void requestSmsPermission() { requestSmsPermissions(); }'''
if old in s:
    s = s.replace(old, new, 1)

# The previous SIM2 patch could be skipped because the JS string itself contained
# the method name. Ensure the actual Java method exists.
if '@JavascriptInterface public void sendSmsFromSim2(String phone,String message)' not in s:
    marker = '        @JavascriptInterface public void sendSms(String phone,String message){'
    method = '''        @JavascriptInterface public void sendSmsFromSim2(String phone,String message){\n            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty()) return;\n            if (Build.VERSION.SDK_INT >= 23) {\n                boolean smsOk = checkSelfPermission(Manifest.permission.SEND_SMS) == PackageManager.PERMISSION_GRANTED;\n                boolean phoneOk = checkSelfPermission(Manifest.permission.READ_PHONE_STATE) == PackageManager.PERMISSION_GRANTED;\n                if(!smsOk || !phoneOk){\n                    runOnUiThread(() -> { Toast.makeText(MainActivity.this,"Allow SMS and Phone permission for SIM 2 SMS.",Toast.LENGTH_LONG).show(); requestSmsPermissions(); });\n                    return;\n                }\n            }\n            try {\n                android.telephony.SubscriptionManager sm = (android.telephony.SubscriptionManager)getSystemService(TELEPHONY_SUBSCRIPTION_SERVICE);\n                java.util.List<android.telephony.SubscriptionInfo> infos = sm.getActiveSubscriptionInfoList();\n                android.telephony.SubscriptionInfo sim2 = null;\n                if(infos!=null){\n                    for(android.telephony.SubscriptionInfo info:infos){\n                        if(info.getSimSlotIndex()==1){ sim2=info; break; }\n                    }\n                }\n                if(sim2==null){\n                    runOnUiThread(() -> Toast.makeText(MainActivity.this,"SIM 2 (Robi) is not active.",Toast.LENGTH_LONG).show());\n                    return;\n                }\n                int subId = sim2.getSubscriptionId();\n                SmsManager sms;\n                if(Build.VERSION.SDK_INT>=31) sms=SmsManager.getDefault().createForSubscriptionId(subId);\n                else sms=SmsManager.getSmsManagerForSubscriptionId(subId);\n                sms.sendTextMessage(phone.trim(),null,message,null,null);\n                runOnUiThread(() -> Toast.makeText(MainActivity.this,"SMS sent from SIM 2 (Robi)",Toast.LENGTH_SHORT).show());\n            } catch(SecurityException e){\n                runOnUiThread(() -> Toast.makeText(MainActivity.this,"Permission denied. Allow SMS + Phone permission.",Toast.LENGTH_LONG).show());\n            } catch(Exception e){\n                runOnUiThread(() -> Toast.makeText(MainActivity.this,"SIM 2 SMS failed: check SIM/network/balance",Toast.LENGTH_LONG).show());\n            }\n        }\n'''
    if marker not in s:
        raise SystemExit('sendSms marker not found')
    s = s.replace(marker, method + marker, 1)
else:
    # Harden an existing method against missing READ_PHONE_STATE permission.
    s = s.replace('if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {', 'if (Build.VERSION.SDK_INT >= 23 && (checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED || checkSelfPermission(Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED)) {', 1)

p.write_text(s, encoding='utf-8')
print('SMS permission + SIM 2 Robi fix applied successfully.')
