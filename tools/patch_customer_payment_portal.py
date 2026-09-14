from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

if 'function customerPortal(){' in s:
    print('customer payment portal already present; skipping')
    raise SystemExit(0)

marker = '</script>'
if marker not in s:
    raise SystemExit('script closing tag not found')

portal = r'''\nfunction customerPortal(){\n  try {\n    var q = new URLSearchParams(location.search);\n    var code = String(q.get('pay') || '').trim();\n    if (!code) return false;\n    var list = Array.isArray(d.customers) ? d.customers : [];\n    var c = list.find(function(x){ return String(x.clientCode || '').trim() === code; });\n    if (!c) {\n      document.getElementById('content').innerHTML = '<div class="section"><h2>STAR COMMUNICATION</h2><p>Customer not found.</p></div>';\n      return true;\n    }\n    var merchant = String(q.get('merchant') || d.settings.merchantNumber || '01897-099850').trim();\n    var username = String(c.pppoeUsername || c.pppoe || c.username || '');\n    var password = String(c.pppoePassword || c.password || '');\n    var total = typeof due === 'function' ? due(c) : Number(c.prevDue || 0) + Number(c.fee || 0);\n    var content = `\n      <section class="section" style="text-align:center;padding:20px">\n        <img src="logo.svg" style="width:82px;height:82px;border-radius:18px">\n        <h1 style="margin:8px 0 2px">STAR COMMUNICATION</h1>\n        <div class="muted">Customer Bill Payment</div>\n      </section>\n      <section class="section">\n        <div class="detail"><span>Customer</span><b>${esc(c.name || 'Customer')}</b></div>\n        <div class="detail"><span>Client Code</span><b>${esc(c.clientCode || c.id)}</b></div>\n        <div class="detail"><span>Username</span><b>${esc(username)}</b></div>\n        <div class="detail"><span>Password</span><b>${esc(password)}</b></div>\n        <div class="detail"><span>Previous Due</span><b>${money(c.prevDue || 0)}</b></div>\n        <div class="detail"><span>Current Bill</span><b>${money(c.fee || 0)}</b></div>\n        <div class="detail"><span>Total Due</span><b style="font-size:20px;color:#c62828">${money(total)}</b></div>\n      </section>\n      <section class="section">\n        <h3>💳 Pay with bKash</h3>\n        <div class="detail"><span>bKash Merchant Number</span><b>${esc(merchant)}</b></div>\n        <p class="muted">Send the bill amount to this merchant number using bKash. Use your Client Code as reference.</p>\n        <button id="copyMerchant" class="btn green full">Copy Merchant Number</button>\n      </section>`;\n    document.getElementById('content').innerHTML = content;\n    var copy = document.getElementById('copyMerchant');\n    if (copy) copy.onclick = function(){\n      if (navigator.clipboard) navigator.clipboard.writeText(merchant).then(function(){toast('Merchant number copied');});\n      else toast(merchant);\n    };\n    return true;\n  } catch(e) {\n    return false;\n  }\n}\n'''

s = s.replace(marker, portal + marker, 1)
p.write_text(s, encoding='utf-8')
print('customer payment portal patched safely')
