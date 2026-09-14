from pathlib import Path
import re

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

# Remove a previously injected customerPortal block, if present.
s = re.sub(r'\nfunction customerPortal\(\)\{.*?\n\}\n(?=function )', '\n', s, flags=re.S)

marker = '</script>'
if marker not in s:
    raise SystemExit('script closing tag not found')

portal = r'''
function customerPortal(){
  try {
    var q = new URLSearchParams(location.search);
    var code = String(q.get('pay') || '').trim();
    if (!code) return false;
    var list = Array.isArray(d.customers) ? d.customers : [];
    var c = list.find(function(x){ return String(x.clientCode || '').trim() === code; });
    if (!c) {
      document.getElementById('content').innerHTML = '<div class="section"><h2>STAR COMMUNICATION</h2><p>Customer not found.</p></div>';
      return true;
    }
    var merchant = String(q.get('merchant') || (d.settings && d.settings.merchantNumber) || '01897-099850').trim();
    var total = typeof due === 'function' ? due(c) : Number(c.prevDue || 0) + Number(c.fee || c.monthlyFee || 0);
    var locationText = String(c.address || c.location || '');
    var packageText = String(c.packageName || c.package || '') + (c.speedMb ? ' ' + c.speedMb + ' Mb' : '');
    var content = `
      <section class="section" style="text-align:center;padding:20px">
        <img src="logo.svg" style="width:82px;height:82px;border-radius:18px">
        <h1 style="margin:8px 0 2px">STAR COMMUNICATION</h1>
        <div class="muted">Customer Bill Payment</div>
      </section>
      <section class="section">
        <div class="detail"><span>Client Code</span><b>${esc(c.clientCode || c.id)}</b></div>
        <div class="detail"><span>Customer Name</span><b>${esc(c.name || 'Customer')}</b></div>
        <div class="detail"><span>Location</span><b>${esc(locationText)}</b></div>
        <div class="detail"><span>Package</span><b>${esc(packageText)}</b></div>
        <div class="detail"><span>Monthly Bill</span><b>${money(c.fee || c.monthlyFee || 0)}</b></div>
        <div class="detail"><span>Previous Due</span><b>${money(c.prevDue || 0)}</b></div>
        <div class="detail"><span>Total Due</span><b style="font-size:20px;color:#c62828">${money(total)}</b></div>
      </section>
      <section class="section" style="text-align:center">
        <h3>💳 bKash Payment</h3>
        <div class="detail"><span>Payment Number</span><b>${esc(merchant)}</b></div>
        <p class="muted">Pay your bill to the number above and use your Client Code as reference.</p>
        <button id="payBkash" class="btn green full">Pay Bill</button>
      </section>`;
    document.getElementById('content').innerHTML = content;
    var pay = document.getElementById('payBkash');
    if (pay) pay.onclick = function(){
      if (navigator.clipboard) navigator.clipboard.writeText(merchant).then(function(){toast('Payment number copied');});
      else toast(merchant);
      setTimeout(function(){
        try { location.href = 'https://bKash.com'; } catch(e) {}
      }, 250);
    };
    return true;
  } catch(e) { return false; }
}
'''

s = s.replace(marker, portal + '\n' + marker, 1)
# Make startup use the portal only when ?pay=... is present.
s = s.replace('render();</script>', "try{if(!customerPortal())render();}catch(e){render();}</script>", 1)
p.write_text(s, encoding='utf-8')
print('customer payment portal updated: code, name, location, package, bill and payment number only')
