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
        @JavascriptInterface public boolean sendSms(String phone,String message){
            if(phone==null||phone.trim().isEmpty()||message==null||message.trim().isEmpty())return false;
            if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread(() -> { Toast.makeText(MainActivity.this,"SMS permission required. Allow it, then press Send SMS again.",Toast.LENGTH_LONG).show(); requestSmsPermission(); });
                return false;
            }
            try{
                SmsManager sms = SmsManager.getDefault();
                sms.sendTextMessage(phone.trim(),null,message,null,null);
                runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS sent using SIM balance",Toast.LENGTH_SHORT).show());
                return true;
            }catch(SecurityException e){runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS permission denied by Android",Toast.LENGTH_LONG).show());return false;}
            catch(Exception e){runOnUiThread(()->Toast.makeText(MainActivity.this,"SMS failed: check SIM/network/balance",Toast.LENGTH_LONG).show());return false;}
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
                    JSONArray arr=packet.optJSONArray("rows"); if(arr==null) arr=new JSONArray();

                    String safe=title.replaceAll("[^A-Za-z0-9 _-]","_");
                    String stamp=new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US).format(new Date());
                    ContentValues values=new ContentValues();
                    values.put(MediaStore.Downloads.DISPLAY_NAME,"STAR-COMMUNICATION-"+safe+"-"+stamp+".pdf");
                    values.put(MediaStore.Downloads.MIME_TYPE,"application/pdf");
                    values.put(MediaStore.Downloads.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS+"/STAR COMMUNICATION");
                    Uri uri=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);
                    if(uri==null) throw new Exception("PDF file could not be created");

                    PdfDocument doc=new PdfDocument();
                    final int W=842,H=595,PER_PAGE=25;
                    Paint p=new Paint(Paint.ANTI_ALIAS_FLAG), bold=new Paint(Paint.ANTI_ALIAS_FLAG);
                    bold.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
                    int totalPages=Math.max(1,(arr.length()+PER_PAGE-1)/PER_PAGE);

                    for(int pageNo=0;pageNo<totalPages;pageNo++){
                        PdfDocument.Page page=doc.startPage(new PdfDocument.PageInfo.Builder(W,H,pageNo+1).create());
                        android.graphics.Canvas cv=page.getCanvas();

                        p.setStyle(Paint.Style.FILL); p.setColor(Color.rgb(8,55,112)); cv.drawRect(0,0,W,72,p);
                        p.setColor(Color.rgb(24,190,86)); cv.drawRect(0,67,W,72,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(21); cv.drawText("STAR COMMUNICATION",22,28,bold);
                        bold.setTextSize(9); cv.drawText("ISP CUSTOMER LIST  •  "+title.toUpperCase(Locale.US),22,49,bold);

                        p.setColor(Color.rgb(20,119,210)); cv.drawRoundRect(700,15,824,52,18,18,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(8); cv.drawText("PAGE "+(pageNo+1)+" / "+totalPages,719,38,bold);

                        int all=arr.length(),paid=0,unpaid=0,expired=0,active=0,inactive=0;
                        for(int q=0;q<all;q++){
                            JSONObject z=arr.getJSONObject(q);
                            String st=z.optString("status","").toLowerCase(Locale.US);
                            double td=z.optDouble("totalDue",0);
                            if(st.equals("expired")) expired++;
                            else if(st.equals("inactive")) inactive++;
                            else if(st.equals("active")) active++;
                            if(td>0) unpaid++; else paid++;
                        }
                        String[] chipNames={"CUSTOMERS","ACTIVE","INACTIVE","EXPIRED","PAID","UNPAID"};
                        int[] chipVals={all,active,inactive,expired,paid,unpaid};
                        int[] chipColors={Color.rgb(22,119,210),Color.rgb(24,170,78),Color.rgb(230,156,20),Color.rgb(215,55,55),Color.rgb(22,145,215),Color.rgb(125,82,190)};
                        int chipX=20;
                        for(int cidx=0;cidx<chipNames.length;cidx++){
                            int cw=(cidx==0?102:94);
                            p.setColor(chipColors[cidx]); cv.drawRoundRect(chipX,80,chipX+cw,101,10,10,p);
                            bold.setColor(Color.WHITE); bold.setTextSize(6.5f); cv.drawText(chipNames[cidx],chipX+8,91,bold);
                            bold.setTextSize(9); cv.drawText(String.valueOf(chipVals[cidx]),chipX+cw-22,94,bold);
                            chipX+=cw+6;
                        }

                        int start=pageNo*PER_PAGE,end=Math.min(arr.length(),start+PER_PAGE);
                        float y=111;
                        for(int j=start;j<end;j++){
                            JSONObject o=arr.getJSONObject(j);
                            int accent=((j%2)==0)?Color.rgb(22,119,210):Color.rgb(24,170,78);
                            p.setColor(Color.WHITE); cv.drawRoundRect(14,y,828,y+17,5,5,p);
                            p.setColor(accent); cv.drawRoundRect(14,y,19,y+17,2,2,p);

                            String name=shortText(o.optString("name","—"),22);
                            String address=shortText(o.optString("address","—"),25);
                            String pkg=shortText(o.optString("pkg","—"),12);
                            String code=shortText(o.optString("id","—"),12);
                            String phone=shortText(o.optString("phone","—"),16);
                            String user=shortText(o.optString("pppoe","—"),18);
                            String pass=shortText(o.optString("pppoePassword","—"),16);
                            String onu=shortText(o.optString("onu","—"),18);
                            String conn=shortText(o.optString("connectionDate","—"),12);
                            String exp=shortText(o.optString("expiry","—"),12);
                            String status=o.optString("status","").toUpperCase(Locale.US);
                            String tt=title.toLowerCase(Locale.US);
                            if(tt.contains("unpaid")) status="UNPAID";
                            else if(tt.contains("expired")) status="EXPIRED";
                            else if(tt.contains("paid")) status="PAID";

                            bold.setColor(Color.rgb(20,45,75)); bold.setTextSize(6.4f);
                            cv.drawText(String.format(Locale.US,"%02d",j+1),25,y+7,bold);
                            cv.drawText(name,48,y+7,bold);
                            p.setColor(Color.rgb(65,80,100)); p.setTextSize(5.8f);
                            cv.drawText("Location: "+address,185,y+7,p);
                            cv.drawText("Package: "+pkg,330,y+7,p);
                            cv.drawText("Bill: ৳"+String.format(Locale.US,"%.0f",o.optDouble("fee",0)),430,y+7,p);
                            cv.drawText("Code: "+code,485,y+7,p);
                            cv.drawText("Number: "+phone,555,y+7,p);

                            int sc=status.equals("PAID")?Color.rgb(22,145,215):status.equals("EXPIRED")?Color.rgb(215,55,55):status.equals("UNPAID")?Color.rgb(230,126,20):Color.rgb(24,170,78);
                            p.setColor(sc); cv.drawRoundRect(752,y+2,824,y+15,7,7,p);
                            bold.setColor(Color.WHITE); bold.setTextSize(5.5f); cv.drawText(shortText(status,10),760,y+10,bold);

                            // Second compact detail line for every customer.
                            p.setColor(Color.rgb(80,95,115)); p.setTextSize(5.7f);
                            cv.drawText("PPPoE User: "+user,48,y+14,p);
                            cv.drawText("Pass: "+pass,205,y+14,p);
                            cv.drawText("ONU MAC: "+onu,320,y+14,p);
                            cv.drawText("Prev Due: ৳"+String.format(Locale.US,"%.0f",o.optDouble("prevDue",0)),465,y+14,p);
                            cv.drawText("Running: ৳"+String.format(Locale.US,"%.0f",o.optDouble("runningBill",0)),555,y+14,p);
                            cv.drawText("Total Due: ৳"+String.format(Locale.US,"%.0f",o.optDouble("totalDue",0)),635,y+14,p);
                            cv.drawText("Conn: "+conn+"  Exp: "+exp,700,y+14,p);
                            y+=18.0f;
                        }

                        p.setColor(Color.rgb(8,55,112)); cv.drawRect(0,568,W,595,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(6.5f);
                        cv.drawText("STAR COMMUNICATION  •  ISP MANAGER",20,583,bold);
                        cv.drawText("25 CUSTOMERS / PAGE  |  Total: "+all+"  |  Page "+(pageNo+1)+" of "+totalPages,600,583,bold);
                        doc.finishPage(page);
                    }

                    OutputStream out=getContentResolver().openOutputStream(uri);
                    if(out==null)throw new Exception("PDF output unavailable");
                    doc.writeTo(out); out.close(); doc.close();

                    Intent view=new Intent(Intent.ACTION_VIEW);
                    view.setDataAndType(uri,"application/pdf");
                    view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_ACTIVITY_NEW_TASK);
                    try{startActivity(view);}
                    catch(Exception ex){
                        Intent share=new Intent(Intent.ACTION_SEND);
                        share.setType("application/pdf");
                        share.putExtra(Intent.EXTRA_STREAM,uri);
                        share.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                        startActivity(Intent.createChooser(share,"Open / Share PDF"));
                    }
                    Toast.makeText(MainActivity.this,"PDF ready: 25 customers per page",Toast.LENGTH_LONG).show();
                }catch(Exception ex){
                    Toast.makeText(MainActivity.this,"PDF তৈরি করতে সমস্যা হয়েছে: "+ex.getMessage(),Toast.LENGTH_LONG).show();
                }
            });
        }
        private String shortText(String s,int max){
            if(s==null||s.trim().isEmpty()) return "—";
            s=s.replace("\n"," ").replace("\r"," ").trim();
            return s.length()>max?s.substring(0,Math.max(1,max-1))+"…":s;
        }
        @JavascriptInterface public void printPage(String title){ runOnUiThread(() -> { try { PrintManager pm=(PrintManager)getSystemService(PRINT_SERVICE); PrintDocumentAdapter adapter=webView.createPrintDocumentAdapter(title==null?"STAR COMMUNICATION":title); pm.print(title==null?"STAR COMMUNICATION":title,adapter,new PrintAttributes.Builder().setMediaSize(PrintAttributes.MediaSize.ISO_A4).setMinMargins(PrintAttributes.Margins.NO_MARGINS).build()); } catch(Exception e){ Toast.makeText(MainActivity.this,"PDF/Print failed. Please try again.",Toast.LENGTH_LONG).show(); } }); }
        @JavascriptInterface public void scheduleExpiry(String phone,String name,String expiry){AutoMessageReceiver.scheduleExpiry(MainActivity.this,phone,name,expiry);}
        @JavascriptInterface public void scheduleMonthEnd(String phone,String name){AutoMessageReceiver.scheduleMonthEnd(MainActivity.this,phone,name);}
        private void requestSmsPermission(){MainActivity.this.requestSmsPermission();}
    }

    @Override public void onBackPressed(){if(webView!=null)webView.evaluateJavascript("typeof appBack==='function' ? appBack() : null",null);else super.onBackPressed();}
}
