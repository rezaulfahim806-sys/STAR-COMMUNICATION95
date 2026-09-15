from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

# Put the Payment Link button directly in every customer card.
card_button = r'''<button class="small" style="background:#7656d6;color:#fff" onclick="customerPaymentLink('${c.id}')">🔗 Payment Link</button>'''
anchor = r'''<button class="small view" onclick="go('details',{id:'${c.id}'})">Details</button>'''
if 'onclick="customerPaymentLink(\'${c.id}\')"' not in s:
    if anchor not in s:
        raise SystemExit('Customer card Details button not found')
    s = s.replace(anchor, anchor + card_button, 1)

# Add Payment Link helpers. The existing Pay Now page/design is left unchanged.
js = r'''<script>
(function(){
  var BASE='https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html';
  function customerById(id){
    var obj=(typeof d!=='undefined'&&d)?d:(window.d||null);
    var list=obj&&Array.isArray(obj.customers)?obj.customers:[];
    return list.find(function(x){return String(x.id)===String(id)||String(x.clientCode||'')===String(id);});
  }
  window.customerPaymentLink=function(id){
    var c=customerById(id);
    if(!c){toast('Customer not found');return '';}
    var obj=(typeof d!=='undefined'&&d)?d:(window.d||{});
    var params=new URLSearchParams();
    params.set('code',String(c.clientCode||c.id||''));
    params.set('name',String(c.name||'Customer'));
    params.set('location',String(c.address||c.location||''));
    params.set('package',String(c.pkg||c.packageName||c.package||''));
    params.set('bill',String(Number(c.fee||c.monthlyFee||0)));
    params.set('prev',String(Number(c.prevDue||0)));
    params.set('total',String(typeof due==='function'?due(c):(Number(c.prevDue||0)+Number(c.fee||c.monthlyFee||0))));
    params.set('merchant',String((obj.settings&&obj.settings.merchantNumber)||'01897-099850'));
    var link=BASE+'?'+params.toString();
    window.open(link,'_blank');
    return link;
  };
  window.copyCustomerPaymentLink=function(id){
    var link=customerPaymentLink(id); if(!link)return;
    if(navigator.clipboard){navigator.clipboard.writeText(link).then(function(){toast('Payment link copied');});}
  };
})();
</script>'''

if 'window.customerPaymentLink=function(id)' not in s:
    s=s.replace('</body>', js+'\n</body>', 1)

p.write_text(s, encoding='utf-8')
print('Payment Link button and customer-specific link fixed')
