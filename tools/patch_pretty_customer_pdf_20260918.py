from pathlib import Path
import re

# 1) Final PDF button code: one customer = one clean numbered card/section.
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
a=s.find("function pdfList(type){")
b=s.find("function render(){",a)
if a<0 or b<0: raise SystemExit("pdfList not found")
fn=r'''function pdfList(type){
 try{
  type=String(type||'all').toLowerCase(); fix();
  var list=(d.customers||[]).slice();
  if(type==='unpaid')list=list.filter(function(c){return due(c)>0});
  if(type==='expired')list=list.filter(function(c){return String(c.status||'').toLowerCase()==='expired'});
  if(type==='paid')list=list.filter(function(c){return due(c)<=0});
  var title=type==='unpaid'?'Unpaid Customer List':type==='expired'?'Expired Customer List':type==='paid'?'Paid Customer List':'All Customer List';
  var x=['TITLE|'+title,'DATE|'+today()+'|MONTH|'+month()+'|COUNT|'+list.length];
  list.forEach(function(c,i){
   x.push('CUSTOMER|'+(i+1));
   [['Customer Name',c.name],['Client ID',c.id],['Mobile',c.phone],['Address',c.address],['Package',c.pkg],['Monthly Bill',money(c.fee)],['PPPoE Username',c.pppoe],['PPPoE Password',c.pppoePassword],['ONU ID',c.onu],['Connection Date',c.connectionDate||'—'],['Expiry Date',c.expiry||'—'],['Previous Due',money(c.prevDue)],['Running Bill',money(billDue(c))],['Total Due',money(due(c))],['Status',String(c.status||'').toUpperCase()]].forEach(function(v){x.push(v[0]+'|'+(v[1]==null?'':v[1]))});
   x.push('END');
  });
  if(window.AndroidBridge&&AndroidBridge.createCustomerPdf){AndroidBridge.createCustomerPdf(title,x.join('\n'));return}
  if(window.AndroidBridge&&AndroidBridge.printPage){var q=document.getElementById('printArea');q.innerHTML='<pre style="font:12px Arial;white-space:pre-wrap">'+esc(x.join('\n'))+'</pre>';q.style.display='block';AndroidBridge.printPage(title);return}
  window.print();
 }catch(e){try{toast('PDF error: '+e.message)}catch(_){alert('PDF error')}}
}'''
p.write_text(s[:a]+fn+s[b:],encoding="utf-8")

# 2) Native Android PDF generator, inserted after all existing Java patches.
j=Path("app/src/main/java/com/starcommunication/isp/MainActivity.java")
t=j.read_text(encoding="utf-8")
imports='''import android.content.ContentValues;
import android.os.Environment;
import android.graphics.Paint;
import android.graphics.pdf.PdfDocument;
import android.provider.MediaStore;
import java.io.OutputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
'''
if "import android.graphics.pdf.PdfDocument;" not in t:
    t=t.replace("import android.graphics.Color;\n","import android.graphics.Color;\n"+imports)

method=r'''
    @JavascriptInterface public void createCustomerPdf(String title,String body){
        runOnUiThread(() -> {
            try{
                String name=(title==null?"Customer_List":title).replaceAll("[^A-Za-z0-9 _-]","_");
                String stamp=new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US).format(new Date());
                ContentValues v=new ContentValues();
                v.put(MediaStore.Downloads.DISPLAY_NAME,"STAR_COMMUNICATION_"+name+"_"+stamp+".pdf");
                v.put(MediaStore.Downloads.MIME_TYPE,"application/pdf");
                v.put(MediaStore.Downloads.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS+"/STAR COMMUNICATION");
                Uri uri=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,v);
                if(uri==null)throw new Exception("file create failed");
                PdfDocument doc=new PdfDocument();
                Paint head=new Paint(1);head.setTextSize(18);head.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);head.setColor(Color.rgb(11,33,69));
                Paint small=new Paint(1);small.setTextSize(9);small.setColor(Color.DKGRAY);
                Paint label=new Paint(1);label.setTextSize(10);label.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);label.setColor(Color.rgb(11,33,69));
                Paint val=new Paint(1);val.setTextSize(10);val.setColor(Color.BLACK);
                Paint border=new Paint(1);border.setStyle(Paint.Style.STROKE);border.setStrokeWidth(2);border.setColor(Color.rgb(180,200,220));
                String[] rows=(body==null?"":body).split("\\n",-1);
                PdfDocument.Page page=null;android.graphics.Canvas c=null;float y=0;int no=1;float top=0;
                for(String row:rows){
                    if(row.startsWith("TITLE|"))continue;
                    if(row.startsWith("DATE|"))continue;
                    if(row.startsWith("CUSTOMER|")){
                        if(page!=null)doc.finishPage(page);
                        page=doc.startPage(new PdfDocument.PageInfo.Builder(842,595,no++).create());c=page.getCanvas();
                        y=25;c.drawText("STAR COMMUNICATION",28,y,head);y+=18;
                        c.drawText(title==null?"Customer List":title,28,y,small);y+=20;
                        top=y;c.drawRoundRect(22,top,820,565,14,14,border);y+=28;
                        c.drawText("CUSTOMER #"+row.substring(9),35,y,label);y+=24;
                        continue;
                    }
                    if(row.equals("END"))continue;
                    int k=row.indexOf('|');if(k<1||c==null)continue;
                    String l=row.substring(0,k),vv=row.substring(k+1);
                    c.drawText(l,38,y,label);c.drawText(vv,190,y,val);y+=19;
                    if(y>545){doc.finishPage(page);page=doc.startPage(new PdfDocument.PageInfo.Builder(842,595,no++).create());c=page.getCanvas();y=28;}
                }
                if(page!=null)doc.finishPage(page);
                OutputStream out=getContentResolver().openOutputStream(uri);if(out==null)throw new Exception("output failed");
                doc.writeTo(out);out.close();doc.close();
                Intent in=new Intent(Intent.ACTION_VIEW);in.setDataAndType(uri,"application/pdf");in.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                try{startActivity(in);}catch(Exception e){Intent sh=new Intent(Intent.ACTION_SEND);sh.setType("application/pdf");sh.putExtra(Intent.EXTRA_STREAM,uri);sh.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);startActivity(Intent.createChooser(sh,"Open Customer PDF"));}
                Toast.makeText(MainActivity.this,"PDF saved in Downloads / STAR COMMUNICATION",Toast.LENGTH_LONG).show();
            }catch(Exception e){Toast.makeText(MainActivity.this,"PDF failed: "+e.getMessage(),Toast.LENGTH_LONG).show();}
        });
    }
'''
if "createCustomerPdf(String title,String body)" not in t:
    pos=t.find("    @JavascriptInterface public void printPage(")
    if pos<0:raise SystemExit("printPage not found")
    t=t[:pos]+method+"\n"+t[pos:]
j.write_text(t,encoding="utf-8")
print("OK")
