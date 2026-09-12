from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
# Remove duplicate Add Customer labels from all generated page HTML except the dedicated Customers page.
# Convert dashboard's left-client card label to the single New Customer action.
s=s.replace('Total Left Client','Add New Customer')
# Hide any explicit add-customer controls on non-customer pages using a CSS class and preserve the customer page button.
s=s.replace('class="btn green" onclick="openSheet(addCustomer','class="btn green customer-only-add" onclick="openSheet(addCustomer')
# Compact overall mobile viewport without removing normal system status/navigation bars.
s=s.replace('.app{max-width:520px;margin:auto;min-height:100vh;','.app{width:100%;max-width:480px;margin:auto;min-height:calc(100vh - 24px);')
s=s.replace('.header{height:62px;','.header{height:56px;')
s=s.replace('.top{height:46px;','.top{height:42px;')
s=s.replace('.content{padding:12px 11px 86px}','.content{padding:10px 10px 78px}')
s=s.replace('height:66px;background:#fff;','height:60px;background:#fff;')
# Durable storage: primary + backup, with recovery on startup.
if "localStorage.setItem(KEY+'_backup'" not in s:
    s=s.replace("function save(){localStorage.setItem(KEY,JSON.stringify(d))}","function save(){const j=JSON.stringify(d);try{localStorage.setItem(KEY,j);localStorage.setItem(KEY+'_backup',j)}catch(e){try{localStorage.setItem(KEY+'_backup',j)}catch(_){} }}",1)
if "localStorage.getItem(KEY+'_backup')" not in s:
    s=s.replace("if(!d)d=JSON.parse(JSON.stringify(DEF));","if(!d){try{d=JSON.parse(localStorage.getItem(KEY+'_backup')||'null')}catch(e){d=null}}if(!d)d=JSON.parse(JSON.stringify(DEF));",1)
p.write_text(s,encoding='utf-8')
