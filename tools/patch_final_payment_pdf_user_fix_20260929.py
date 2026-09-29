from pathlib import Path
import re

# Final payment-link SMS hard-fix.
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
new_sms = r'''function sendPaymentLinkSms(){
 let x=window.__starPay;
 if(!x||!x.link){toast('Payment link not found');return}
 let phone=String(x.phone||'').trim();
 if(!phone){toast('Customer mobile number নেই');return}
 let msg='STAR COMMUNICATION\\nYour bill payment link:\\n'+x.link;
 try{
   if(window.AndroidBridge&&typeof AndroidBridge.sendSms==='function'){
     let ok=AndroidBridge.sendSms(phone,msg);
     if(ok){closeSheet();toast('Payment link SMS sending...');return}
   }
 }catch(e){}
 try{
   if(window.AndroidBridge&&typeof AndroidBridge.openSmsComposer==='function'){
     let ok=AndroidBridge.openSmsComposer(phone,msg);
     if(ok){closeSheet();toast('SMS composer opened');return}
   }
 }catch(e){}
 try{ location.href='smsto:'+encodeURIComponent(phone)+'?body='+encodeURIComponent(msg); }
 catch(e){toast('SMS service unavailable')}
}
'''
s2,n=re.subn(r"function sendPaymentLinkSms\(\)\{.*?\}\nfunction startup\(\)",new_sms+"function startup()",s,count=1,flags=re.S)
if n!=1: raise SystemExit("payment link SMS function not found")
p.write_text(s2,encoding="utf-8")

# Final PDF readability/layout hard-fix: make bill, mobile/number, package and
# other key fields explicit horizontal columns. Keep the existing native PDF
# generation and replace only the drawing block.
p=Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
s=p.read_text(encoding="utf-8")
start=s.find("public void createCustomerPdf(String payload){")
end=s.find("        private String shortText",start)
if start<0 or end<0: raise SystemExit("createCustomerPdf block not found")
method = r'''public void createCustomerPdf(String payload){
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
                    final int W=842,H=595,PER_PAGE=8;
                    Paint p=new Paint(Paint.ANTI_ALIAS_FLAG), bold=new Paint(Paint.ANTI_ALIAS_FLAG);
                    bold.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
                    int totalPages=Math.max(1,(arr.length()+PER_PAGE-1)/PER_PAGE);

                    for(int pageNo=0;pageNo<totalPages;pageNo++){
                        PdfDocument.Page page=doc.startPage(new PdfDocument.PageInfo.Builder(W,H,pageNo+1).create());
                        android.graphics.Canvas cv=page.getCanvas();
                        p.setColor(Color.rgb(7,66,128)); cv.drawRect(0,0,W,70,p);
                        p.setColor(Color.rgb(37,197,92)); cv.drawRect(0,66,W,70,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(21); cv.drawText("STAR COMMUNICATION",18,28,bold);
                        bold.setTextSize(8.5f); cv.drawText("ISP CUSTOMER LIST  •  "+title.toUpperCase(Locale.US),18,48,bold);
                        bold.setTextSize(7.5f); cv.drawText("PAGE "+(pageNo+1)+" / "+totalPages,760,35,bold);

                        float top=82;
                        p.setColor(Color.rgb(7,66,128)); cv.drawRoundRect(10,top,832,top+31,5,5,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(6.4f);
                        cv.drawText("#",16,top+12,bold);
                        cv.drawText("CUSTOMER",38,top+12,bold);
                        cv.drawText("MOBILE / NUMBER",142,top+12,bold);
                        cv.drawText("PACKAGE",246,top+12,bold);
                        cv.drawText("BILL",316,top+12,bold);
                        cv.drawText("CLIENT CODE",360,top+12,bold);
                        cv.drawText("STATUS",450,top+12,bold);
                        cv.drawText("TOTAL DUE",515,top+12,bold);
                        cv.drawText("CONNECTION",590,top+12,bold);
                        cv.drawText("EXPIRY",665,top+12,bold);
                        cv.drawText("ADDRESS",730,top+12,bold);
                        cv.drawText("PPPoE USER / PASS / ONU",38,top+24,bold);

                        int startRow=pageNo*PER_PAGE,endRow=Math.min(arr.length(),startRow+PER_PAGE);
                        float y=120;
                        for(int j=startRow;j<endRow;j++){
                            JSONObject o=arr.getJSONObject(j);
                            p.setColor(j%2==0?Color.WHITE:Color.rgb(240,248,244)); cv.drawRoundRect(10,y,832,y+54f,5,5,p);
                            p.setColor(j%2==0?Color.rgb(20,120,205):Color.rgb(26,175,84)); cv.drawRoundRect(10,y,15,y+54f,2,2,p);
                            String name=shortText(o.optString("name","—"),15);
                            String phone=shortText(o.optString("phone","—"),14);
                            String pkg=shortText(o.optString("pkg","—"),9);
                            String code=shortText(o.optString("id","—"),10);
                            String status=o.optString("status","").toUpperCase(Locale.US);
                            String tt=title.toLowerCase(Locale.US);
                            if(tt.contains("unpaid")) status="UNPAID"; else if(tt.contains("expired")) status="EXPIRED"; else if(tt.contains("paid")) status="PAID";
                            String address=shortText(o.optString("address","—"),18);
                            String conn=shortText(o.optString("connectionDate","—"),10);
                            String exp=shortText(o.optString("expiry","—"),10);
                            String user=shortText(o.optString("pppoe","—"),13);
                            String pass=shortText(o.optString("pppoePassword","—"),11);
                            String onu=shortText(o.optString("onu","—"),13);
                            bold.setColor(Color.rgb(15,45,75)); bold.setTextSize(7.7f);
                            cv.drawText(String.format(Locale.US,"%02d",j+1),16,y+15,bold);
                            cv.drawText(name,38,y+15,bold);
                            p.setColor(Color.rgb(45,65,85)); p.setTextSize(7.1f);
                            cv.drawText(phone,142,y+15,p);
                            cv.drawText(pkg,246,y+15,p);
                            cv.drawText("৳"+String.format(Locale.US,"%.0f",o.optDouble("fee",0)),316,y+15,p);
                            cv.drawText(code,360,y+15,p);
                            int sc=status.equals("PAID")?Color.rgb(20,145,215):status.equals("EXPIRED")?Color.rgb(215,55,55):status.equals("UNPAID")?Color.rgb(235,130,20):Color.rgb(25,175,82);
                            p.setColor(sc); cv.drawRoundRect(450,y+4,502,y+19,8,8,p);
                            bold.setColor(Color.WHITE); bold.setTextSize(5.7f); cv.drawText(shortText(status,8),455,y+14,bold);
                            p.setColor(Color.rgb(45,65,85)); p.setTextSize(7.1f);
                            cv.drawText("৳"+String.format(Locale.US,"%.0f",o.optDouble("totalDue",0)),515,y+15,p);
                            cv.drawText(conn,590,y+15,p);
                            cv.drawText(exp,665,y+15,p);
                            cv.drawText(address,730,y+15,p);
                            cv.drawText("USER: "+user,38,y+34,p);
                            cv.drawText("PASS: "+pass,180,y+34,p);
                            cv.drawText("ONU: "+onu,300,y+34,p);
                            cv.drawText("PREV: ৳"+String.format(Locale.US,"%.0f",o.optDouble("prevDue",0)),430,y+34,p);
                            cv.drawText("RUNNING: ৳"+String.format(Locale.US,"%.0f",o.optDouble("runningBill",0)),535,y+34,p);
                            cv.drawText("TOTAL DUE: ৳"+String.format(Locale.US,"%.0f",o.optDouble("totalDue",0)),680,y+34,p);
                            y+=57f;
                        }
                        p.setColor(Color.rgb(7,66,128)); cv.drawRect(0,573,W,595,p);
                        bold.setColor(Color.WHITE); bold.setTextSize(6.5f);
                        cv.drawText("STAR COMMUNICATION  •  MOBILE + BILL + PACKAGE IN SEPARATE COLUMNS",18,586,bold);
                        cv.drawText("TOTAL "+arr.length()+"  |  PAGE "+(pageNo+1)+" OF "+totalPages,700,586,bold);
                        doc.finishPage(page);
                    }
                    OutputStream out=getContentResolver().openOutputStream(uri);
                    if(out==null) throw new Exception("PDF output unavailable");
                    doc.writeTo(out); out.close(); doc.close();
                    Intent view=new Intent(Intent.ACTION_VIEW); view.setDataAndType(uri,"application/pdf");
                    view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_ACTIVITY_NEW_TASK);
                    try{startActivity(view);}catch(Exception ex){
                        Intent share=new Intent(Intent.ACTION_SEND); share.setType("application/pdf"); share.putExtra(Intent.EXTRA_STREAM,uri);
                        share.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION); startActivity(Intent.createChooser(share,"Open / Share PDF"));
                    }
                    Toast.makeText(MainActivity.this,"PDF ready: clear side-by-side columns",Toast.LENGTH_LONG).show();
                }catch(Exception ex){Toast.makeText(MainActivity.this,"PDF তৈরি করতে সমস্যা হয়েছে: "+ex.getMessage(),Toast.LENGTH_LONG).show();}
            });
        }
        '''
s=s[:start]+method+s[end:]
p.write_text(s,encoding="utf-8")
print("patched")
