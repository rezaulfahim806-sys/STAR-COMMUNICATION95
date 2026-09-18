from pathlib import Path
import re

p = Path("app/src/main/assets/index.html")
s = p.read_text(encoding="utf-8")

# Replace the final PDF function directly, so it is independent of earlier patches.
new_pdf = r"""function pdfList(type){
 fix();
 type=String(type||'all').toLowerCase();
 var list=(d.customers||[]).slice();
 if(type==='unpaid') list=list.filter(function(c){return due(c)>0});
 else if(type==='expired') list=list.filter(function(c){return String(c.status||'').toLowerCase()==='expired'});
 else if(type==='paid') list=list.filter(function(c){return due(c)<=0});
 var title=type==='unpaid'?'Unpaid Customer List':type==='expired'?'Expired Customer List':type==='paid'?'Paid Customer List':'All Customer List';
 var rows=list.map(function(c,i){
   var paidAmt=paid(c), fee=Number(c.fee||0);
   var running=Math.max(0,fee-Math.min(fee,paidAmt));
   var total=due(c);
   return '<tr><td>'+(i+1)+'</td><td><b>'+esc(c.name||'')+'</b><br><small>Client ID: '+esc(c.id||'')+'</small></td><td>'+esc(c.phone||'')+'</td><td>'+esc(c.address||'')+'</td><td>'+esc(c.pkg||'')+'</td><td>'+money(fee)+'</td><td>'+esc(c.pppoe||'')+'</td><td>'+esc(c.pppoePassword||'')+'</td><td>'+esc(c.onu||'')+'</td><td>'+esc(c.connectionDate||'')+'</td><td>'+esc(c.expiry||'')+'</td><td>'+money(c.prevDue)+'</td><td>'+money(running)+'</td><td>'+money(total)+'</td><td>'+String(c.status||'').toUpperCase()+'</td></tr>';
 });
 var p=document.getElementById('printArea');
 if(!p){toast('PDF area unavailable');return}
 p.innerHTML='<div style="font-family:Arial,sans-serif"><h1 style="margin:0 0 5px;text-align:center">STAR COMMUNICATION</h1><h2 style="margin:0 0 8px;text-align:center">'+title+'</h2><div style="font-size:11px;margin-bottom:10px">Month: '+month()+' | Generated: '+today()+' | Total Customers: '+list.length+'</div><table style="width:100%;border-collapse:collapse;font-size:8px"><thead><tr><th>#</th><th>Customer / Client ID</th><th>Mobile</th><th>Address</th><th>Package</th><th>Monthly Bill</th><th>PPPoE Username</th><th>PPPoE Password</th><th>ONU ID</th><th>Connection Date</th><th>Expiry Date</th><th>Previous Due</th><th>Running Bill</th><th>Total Due</th><th>Status</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
 p.style.display='block';
 setTimeout(function(){
   var ok=false;
   try{
     if(window.AndroidBridge && typeof AndroidBridge.printPage==='function'){AndroidBridge.printPage(title);ok=true}
   }catch(e){}
   if(!ok){try{window.print()}catch(e){toast('PDF print failed')}}
   setTimeout(function(){p.style.display='none'},8000);
 },150);
}"""
s2, n = re.subn(r"function pdfList\(type\)\{.*?\}\s*function render\(\)", new_pdf + "\nfunction render()", s, count=1, flags=re.S)
if n != 1:
    raise SystemExit("Could not locate pdfList function")

# Add a final event/handler layer for the SMS composer and PDF buttons.
inject = r"""
/* FINAL PDF + SMS FIX */
(function(){
 if(window.__starPdfSmsFix20260918)return;
 window.__starPdfSmsFix20260918=true;

 window.starSendCustomerSMS=function(){
   try{
     var sh=document.getElementById('sheet');
     if(!sh){toast('SMS window not found');return}
     var ta=sh.querySelector('textarea');
     var msg=ta?String(ta.value||'').trim():'';
     if(!msg){toast('Write a message first');return}
     var txt=sh.innerText||'';
     var m=txt.match(/(?:To:\s*[^\n]*?\s*[•·-]\s*)?(\+?\d[\d\s-]{8,})/);
     var phone=m?m[1].replace(/[\s-]/g,''):'';
     if(!phone){toast('Customer mobile number not found');return}
     if(window.AndroidBridge&&typeof AndroidBridge.sendSms==='function'){
       AndroidBridge.sendSms(phone,msg);
       toast('SMS sending...');
     }else{
       window.location.href='sms:'+phone+'?body='+encodeURIComponent(msg);
     }
   }catch(e){toast('SMS failed')}
 };

 document.addEventListener('click',function(ev){
   var b=ev.target&&ev.target.closest?ev.target.closest('button'):null;
   if(!b)return;
   var t=(b.innerText||b.textContent||'').trim();

   if(b.classList.contains('pdfbtn')){
     ev.preventDefault(); ev.stopImmediatePropagation();
     var all=[].slice.call(document.querySelectorAll('.pdfbtn'));
     var i=all.indexOf(b);
     var type=['all','unpaid','expired','paid'][i]||'all';
     try{pdfList(type)}catch(e){toast('PDF generation failed')}
     return;
   }

   if(/Send SMS/i.test(t) && document.getElementById('modal') && document.getElementById('modal').classList.contains('show')){
     ev.preventDefault(); ev.stopImmediatePropagation();
     window.starSendCustomerSMS();
   }
 },true);

 var mo=new MutationObserver(function(){
   var sh=document.getElementById('sheet');
   if(!sh)return;
   var h=sh.querySelector('h3');
   if(h && /Send SMS/i.test(h.textContent||'')){
     var bs=sh.querySelectorAll('button');
     for(var i=0;i<bs.length;i++){
       if(/Send SMS/i.test(bs[i].textContent||'')){
         bs[i].onclick=null;
         bs[i].removeAttribute('onclick');
         bs[i].addEventListener('click',function(e){e.preventDefault();e.stopPropagation();window.starSendCustomerSMS()});
       }
     }
   }
 });
 try{mo.observe(document.body,{childList:true,subtree:true})}catch(e){}
})();
"""
s2 = s2.replace("</script></body></html>", inject + "
</script></body></html>")
p.write_text(s2, encoding="utf-8")
print("patched", n)
