from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

script=r'''<script>
(function(){
  if(window.__starFinalCustomerButtons20260918)return;
  window.__starFinalCustomerButtons20260918=true;

  function byId(id){
    return (d.customers||[]).find(function(c){return String(c.id)===String(id)||String(c.clientCode||'')===String(id);});
  }
  function code(c){
    if(window.ensureClientCode)return window.ensureClientCode(c);
    if(c.clientCode)return String(c.clientCode);
    var n=(d.customers||[]).length+1;
    c.clientCode='SC'+String(n).padStart(3,'0'); save(); return c.clientCode;
  }
  function payment(id){
    if(typeof generatePaymentLink==='function'){generatePaymentLink(id);return;}
    toast('Payment Link feature not ready');
  }
  window.card=function(c){
    code(c);
    var dv=typeof due==='function'?due(c):Number(c.prevDue||0)+Number(c.fee||0);
    var pp=typeof paid==='function'?paid(c):0;
    var run=Math.max(0,Number(c.fee||0)-Math.min(Number(c.fee||0),pp));
    var num=esc(c.phone||'');
    return '<div class="customer">'+
      '<div class="cmain"><div class="avatar">'+esc((c.name||'?')[0].toUpperCase())+'</div>'+
      '<div class="grow"><div class="name">'+esc(c.name||'Customer')+'</div>'+
      '<div class="muted"><b>'+esc(code(c))+'</b> • '+num+' • '+esc(c.pkg||'')+'</div></div>'+
      '<span class="badge '+esc(c.status||'inactive')+'">'+String(c.status||'').toUpperCase()+'</span></div>'+
      '<div class="actions">'+(typeof billBadge==='function'?billBadge(c):'')+'</div>'+
      '<div class="detail"><span>Connection Date</span><b>'+esc(c.connectionDate||'—')+'</b></div>'+
      '<div class="detail"><span>Expiry Date</span><b>'+esc(c.expiry||'—')+'</b></div>'+
      '<div class="detail"><span>Monthly Bill</span><b>'+money(c.fee)+'</b></div>'+
      '<div class="detail"><span>Previous Due</span><b>'+money(c.prevDue)+'</b></div>'+
      '<div class="detail"><span>Running Bill</span><b>'+money(run)+'</b></div>'+
      '<div class="detail"><span>Total Due</span><b>'+money(dv)+'</b></div>'+
      '<div class="actions">'+
      '<button class="small call" onclick="callCustomer(\''+num+'\')">📞 Phone</button>'+
      '<button class="small wa" onclick="waCustomer(\''+num+'\')">WhatsApp</button>'+
      '<button class="small view" onclick="go(\'details\',{id:\''+String(c.id).replace(/'/g,"\\'")+'\'})">View Customer</button>'+
      '<button class="small editbtn" onclick="editCustomer(\''+String(c.id).replace(/'/g,"\\'")+'\')">✏️ Edit Customer</button>'+
      '<button class="small linkbtn" onclick="generatePaymentLink(\''+String(c.id).replace(/'/g,"\\'")+'\')">🔗 Payment Link</button>'+
      '<button class="small view" onclick="starCustomerSms(\''+String(c.id).replace(/'/g,"\\'")+'\')">📩 SMS</button>'+
      '<button class="small pay" onclick="payCustomer(\''+String(c.id).replace(/'/g,"\\'")+'\')">হিসাব / Pay</button>'+
      '</div></div>';
  };

  function wire(){
    if(typeof page==='undefined'||page!=='customers')return;
    document.querySelectorAll('.pdfbtn').forEach(function(b,i){
      var type=['all','unpaid','expired','paid'][i];
      b.onclick=function(){if(typeof pdfList==='function')pdfList(type);else if(typeof exportCustomerPDF==='function')exportCustomerPDF(type);};
    });
  }
  var oldCustomers=window.customers;
  if(oldCustomers){
    window.customers=function(){var h=oldCustomers.apply(this,arguments);return h;};
  }
  var oldRender=window.render;
  if(oldRender&&!window.__starFinalRenderWrap){
    window.__starFinalRenderWrap=true;
    window.render=function(){oldRender();setTimeout(wire,30);};
  }
  setTimeout(function(){try{render();}catch(e){}},50);
})();
</script>
'''
if '__starFinalCustomerButtons20260918' not in s:
    s=s.replace('</body>',script+'</body>',1)
p.write_text(s,encoding='utf-8')
print('final customer buttons patch written')
