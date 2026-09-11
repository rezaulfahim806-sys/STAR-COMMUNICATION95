from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
head='<link rel="manifest" href="manifest.webmanifest"><meta name="apple-mobile-web-app-capable" content="yes">'
if 'manifest.webmanifest' not in s:s=s.replace('</head>',head+'</head>',1)
fn="function paymentLink(c){let code=String(c.clientCode||c.id||'').trim();if(!code){toast('Client Code required');return}let merchant=String(d.settings.merchantNumber||'01897-099850').trim();let url=location.href.split('?')[0]+'?pay='+encodeURIComponent(code)+'&merchant='+encodeURIComponent(merchant);if(navigator.share){navigator.share({title:'STAR COMMUNICATION Bill Payment',text:'Client Code: '+code+'\\nMerchant: '+merchant,url:url}).catch(()=>{})}else if(navigator.clipboard){navigator.clipboard.writeText(url).then(()=>toast('Payment link copied')).catch(()=>prompt('Payment link',url))}else prompt('Payment link',url)}"
if 'function paymentLink(c)' not in s:s=s.replace('function payCustomer(id){',fn+'function payCustomer(id){',1)
needle='<button class="small view" onclick="go(\'details\',{id:\'${c.id}\'})">Details</button>'
if 'Payment Link' not in s and needle in s:s=s.replace(needle,needle+'<button class="small view" onclick="paymentLink(d.customers.find(x=>String(x.id)===String(\'${c.id}\')))\">Payment Link</button>',1)
old='<button class="small pay" onclick="payCustomer(\'${c.id}\')">Customer Bill Payment</button>'
if old in s:s=s.replace(old,old+'<button class="small view" onclick="paymentLink(c)">Payment Link</button>',1)
oldb='<div class="section"><h3>Company Merchant Number</h3>'
newb='<div class="section"><h3>🔗 Customer Payment Link</h3><div class="muted">Each customer link carries the Client Code. The merchant number is shown for payment instructions.</div></div>'+oldb
if '🔗 Customer Payment Link' not in s and oldb in s:s=s.replace(oldb,newb,1)
if 'navigator.serviceWorker.register' not in s:s=s.replace("render();</script>","try{if('serviceWorker' in navigator&&location.protocol!=='file:')navigator.serviceWorker.register('./sw.js').catch(function(){})}catch(e){}render();</script>",1)
p.write_text(s,encoding='utf-8')
print('web payment and PWA patch applied')
