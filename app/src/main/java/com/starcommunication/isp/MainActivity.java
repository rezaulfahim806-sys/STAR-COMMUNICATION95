package com.starcommunication.isp;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.ContentValues;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.graphics.Paint;
import android.graphics.pdf.PdfDocument;
import android.provider.MediaStore;
import java.io.OutputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import android.telephony.SmsManager;
import org.json.JSONArray;
import org.json.JSONObject;
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
            @Override public void onPageFinished(WebView v,String u){super.onPageFinished(v,u);migrateStorage(v);injectFeatures();}
        });
        webView.loadUrl("file:///android_asset/index.html");
    }

    private void migrateStorage(WebView v){
        String js="javascript:(function(){try{"+
                "if(localStorage.getItem('star_communication_migration_v1_v2_done')==='1')return;"+
                "var oldRaw=localStorage.getItem('star_communication_final_v1');if(!oldRaw)return;"+
                "var oldData=JSON.parse(oldRaw),newRaw=localStorage.getItem('star_communication_final_v2'),newData=null;"+
                "try{newData=newRaw?JSON.parse(newRaw):null}catch(e){newData=null}"+
                "if(!newData||!Array.isArray(newData.customers)||newData.customers.length===0){localStorage.setItem('star_communication_final_v2',oldRaw)}else{"+
                "['customers','payments','expenses','pending','history'].forEach(function(k){var a=Array.isArray(newData[k])?newData[k]:[],b=Array.isArray(oldData[k])?oldData[k]:[],seen={};a.forEach(function(x){if(x&&x.id!=null)seen[String(x.id)]=1});b.forEach(function(x){if(!x||x.id==null||!seen[String(x.id)]){a.push(x);if(x&&x.id!=null)seen[String(x.id)]=1}});newData[k]=a});"+
                "newData.settings=Object.assign({},oldData.settings||{},newData.settings||{});"+
                "if(oldData.settings&&oldData.settings.olt)newData.settings.olt=Object.assign({},oldData.settings.olt||{},(newData.settings||{}).olt||{});"+
                "localStorage.setItem('star_communication_final_v2',JSON.stringify(newData));}"+
                "localStorage.setItem('star_communication_migration_v1_v2_done','1');location.reload();"+
                "}catch(e){console.log('STAR migration failed',e)}})();";
        v.evaluateJavascript(js,null);
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
        @JavascriptInterface public void saveCustomerPdf(String fileName,String body){
            String title=fileName==null?"Customer List":fileName.replace("STAR_COMMUNICATION_","").replace(".pdf","").replace("_"," ");
            try{
                JSONObject packet=new JSONObject();
                packet.put("title",title);
                packet.put("rows",new JSONArray(body==null?"[]":body));
                createCustomerPdf(packet.toString());
            }catch(Exception e){ Toast.makeText(MainActivity.this,"PDF data error: "+e.getMessage(),Toast.LENGTH_LONG).show(); }
        }
        @JavascriptInterface public void createCustomerPdf(String payload){
            runOnUiThread(() -> {
                if (Build.VERSION.SDK_INT < 29) { printPage("STAR COMMUNICATION"); return; }
                try {
                    JSONObject packet=new JSONObject(payload==null?"{}":payload);
                    String title=packet.optString("title","Customer List");
                    JSONArray arr=packet.optJSONArray("rows");
                    if(arr==null) arr=new JSONArray();
                    String safe=(title==null||title.trim().isEmpty()?"Customer List":title).replaceAll("[^A-Za-z0-9 _-]","_");
                    String stamp=new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US).format(new Date());
                    ContentValues values=new ContentValues();
                    values.put(MediaStore.Downloads.DISPLAY_NAME,"STAR-COMMUNICATION-"+safe+"-"+stamp+".pdf");
                    values.put(MediaStore.Downloads.MIME_TYPE,"application/pdf");
                    values.put(MediaStore.Downloads.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS+"/STAR COMMUNICATION");
                    Uri uri=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);
                    if(uri==null) throw new Exception("PDF file could not be created");

                    PdfDocument doc=new PdfDocument();
                    final int W=842,H=595;
                    Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
                    Paint bold=new Paint(Paint.ANTI_ALIAS_FLAG);
                    Paint white=new Paint(Paint.ANTI_ALIAS_FLAG);
                    bold.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
                    white.setColor(Color.WHITE);

                    for(int i=0;i<Math.max(1,arr.length());i++){
                        PdfDocument.Page page=doc.startPage(new PdfDocument.PageInfo.Builder(W,H,i+1).create());
                        android.graphics.Canvas cv=page.getCanvas();

                        // Professional header
                        p.setColor(Color.rgb(11,33,69)); cv.drawRect(0,0,W,82,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(24); cv.drawText("STAR COMMUNICATION",28,34,bold);
                        bold.setTextSize(12); cv.drawText(title==null?"Customer List":title,28,57,bold);
                        p.setColor(Color.rgb(22,119,210)); cv.drawRect(650,18,814,64,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(14); cv.drawText("CUSTOMER #"+String.format(Locale.US,"%03d",i+1),672,47,bold);

                        if(arr.length()==0){
                            p.setColor(Color.DKGRAY); p.setTextSize(16); cv.drawText("No customers found.",30,125,p);
                            doc.finishPage(page); continue;
                        }

                        JSONObject o=arr.getJSONObject(i);
                        p.setColor(Color.WHITE); cv.drawRect(22,98,820,570,p);
                        p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(1.2f); p.setColor(Color.rgb(215,222,232)); cv.drawRoundRect(22,98,820,570,12,12,p); p.setStyle(Paint.Style.FILL);

                        bold.setColor(Color.rgb(23,37,58)); bold.setTextSize(19); cv.drawText(o.optString("name","Customer"),40,128,bold);
                        p.setTextSize(11); p.setColor(Color.rgb(105,117,136)); cv.drawText("Client ID: "+o.optString("id","—"),40,148,p);
                        String status=o.optString("status","").toUpperCase(Locale.US);
                        int sc=Color.rgb(21,128,61);
                        if("EXPIRED".equals(status)) sc=Color.rgb(185,28,28);
                        else if("INACTIVE".equals(status)) sc=Color.rgb(71,85,105);
                        else if("UNPAID".equals(status)) sc=Color.rgb(194,65,12);
                        p.setColor(sc); cv.drawRoundRect(690,112,802,145,16,16,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(10); cv.drawText(status,710,133,bold);

                        // Section helper
                        p.setColor(Color.rgb(242,246,250)); cv.drawRoundRect(38,166,804,191,7,7,p);
                        bold.setColor(Color.rgb(11,79,145)); bold.setTextSize(11); cv.drawText("CUSTOMER INFORMATION",50,183,bold);
                        p.setColor(Color.rgb(242,246,250)); cv.drawRoundRect(38,202,418,324,8,8,p);
                        cv.drawRoundRect(430,202,804,324,8,8,p);
                        bold.setColor(Color.rgb(23,37,58)); bold.setTextSize(10);
                        p.setColor(Color.rgb(23,37,58)); p.setTextSize(10);
                        cv.drawText("Mobile / WhatsApp",52,220,bold); cv.drawText(o.optString("phone","—"),52,237,p);
                        cv.drawText("Address",52,257,bold); cv.drawText(o.optString("address","—"),52,274,p);
                        cv.drawText("Package",52,294,bold); cv.drawText(o.optString("pkg","—"),52,311,p);
                        cv.drawText("Monthly Bill",444,220,bold); cv.drawText("৳"+String.format(Locale.US,"%,.0f",o.optDouble("fee",0)),444,237,p);
                        cv.drawText("Connection Date",444,257,bold); cv.drawText(o.optString("connectionDate","—"),444,274,p);
                        cv.drawText("Expiry Date",444,294,bold); cv.drawText(o.optString("expiry","—"),444,311,p);

                        p.setColor(Color.rgb(242,246,250)); cv.drawRoundRect(38,336,804,361,7,7,p);
                        bold.setColor(Color.rgb(11,79,145)); bold.setTextSize(11); cv.drawText("INTERNET / ONU INFORMATION",50,353,bold);
                        p.setColor(Color.rgb(242,246,250)); cv.drawRoundRect(38,372,804,431,8,8,p);
                        p.setColor(Color.rgb(23,37,58)); p.setTextSize(10);
                        cv.drawText("PPPoE Username",52,392,bold); cv.drawText(o.optString("pppoe","—"),52,408,p);
                        cv.drawText("PPPoE Password",300,392,bold); cv.drawText(o.optString("pppoePassword","—"),300,408,p);
                        cv.drawText("ONU ID",600,392,bold); cv.drawText(o.optString("onu","—"),600,408,p);

                        p.setColor(Color.rgb(242,246,250)); cv.drawRoundRect(38,443,804,468,7,7,p);
                        bold.setColor(Color.rgb(11,79,145)); bold.setTextSize(11); cv.drawText("BILLING SUMMARY",50,460,bold);
                        p.setColor(Color.rgb(255,248,235)); cv.drawRoundRect(38,479,280,548,8,8,p);
                        p.setColor(Color.rgb(239,246,255)); cv.drawRoundRect(292,479,534,548,8,8,p);
                        p.setColor(Color.rgb(254,242,242)); cv.drawRoundRect(546,479,804,548,8,8,p);
                        p.setColor(Color.rgb(23,37,58)); p.setTextSize(10);
                        cv.drawText("Previous Due",52,499,bold); cv.drawText("৳"+String.format(Locale.US,"%,.0f",o.optDouble("prevDue",0)),52,524,bold);
                        cv.drawText("Running Bill",306,499,bold); cv.drawText("৳"+String.format(Locale.US,"%,.0f",o.optDouble("runningBill",0)),306,524,bold);
                        bold.setColor(Color.rgb(185,28,28)); cv.drawText("TOTAL DUE",560,499,bold); cv.drawText("৳"+String.format(Locale.US,"%,.0f",o.optDouble("totalDue",0)),560,524,bold);
                        p.setColor(Color.rgb(105,117,136)); p.setTextSize(8); cv.drawText("Generated: "+new SimpleDateFormat("dd MMM yyyy, hh:mm a",Locale.US).format(new Date()),40,563,p);
                        cv.drawText("Page "+(i+1)+" / "+Math.max(1,arr.length()),744,563,p);
                        doc.finishPage(page);
                    }

                    OutputStream out=getContentResolver().openOutputStream(uri);
                    if(out==null) throw new Exception("PDF output unavailable");
                    doc.writeTo(out); out.close(); doc.close();

                    Intent view=new Intent(Intent.ACTION_VIEW);
                    view.setDataAndType(uri,"application/pdf");
                    view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_ACTIVITY_NEW_TASK);
                    try{startActivity(view);}
                    catch(Exception ex){Intent share=new Intent(Intent.ACTION_SEND);share.setType("application/pdf");share.putExtra(Intent.EXTRA_STREAM,uri);share.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);startActivity(Intent.createChooser(share,"Open / Share PDF"));}
                    Toast.makeText(MainActivity.this,"Professional PDF saved in Downloads / STAR COMMUNICATION",Toast.LENGTH_LONG).show();
                }catch(Exception ex){
                    Toast.makeText(MainActivity.this,"PDF তৈরি করতে সমস্যা হয়েছে: "+ex.getMessage(),Toast.LENGTH_LONG).show();
                }
            });
        }
        @JavascriptInterface public void printPage(String title){ runOnUiThread(() -> { try { PrintManager pm=(PrintManager)getSystemService(PRINT_SERVICE); PrintDocumentAdapter adapter=webView.createPrintDocumentAdapter(title==null?"STAR COMMUNICATION":title); pm.print(title==null?"STAR COMMUNICATION":title,adapter,new PrintAttributes.Builder().setMediaSize(PrintAttributes.MediaSize.ISO_A4).setMinMargins(PrintAttributes.Margins.NO_MARGINS).build()); } catch(Exception e){ Toast.makeText(MainActivity.this,"PDF/Print failed. Please try again.",Toast.LENGTH_LONG).show(); } }); }
        @JavascriptInterface public void scheduleExpiry(String phone,String name,String expiry){AutoMessageReceiver.scheduleExpiry(MainActivity.this,phone,name,expiry);}
        @JavascriptInterface public void scheduleMonthEnd(String phone,String name){AutoMessageReceiver.scheduleMonthEnd(MainActivity.this,phone,name);}
        private void requestSmsPermission(){MainActivity.this.requestSmsPermission();}
    }

    @Override public void onBackPressed(){if(webView!=null)webView.evaluateJavascript("typeof appBack==='function' ? appBack() : null",null);else super.onBackPressed();}
}
