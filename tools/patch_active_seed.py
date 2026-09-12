from pathlib import Path
import csv, json

HTML = Path('app/src/main/assets/index.html')
CSV = Path('app/src/main/assets/active_customers.csv')
text = HTML.read_text(encoding='utf-8')
rows = []
with CSV.open('r', encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        code = (r.get('Client Code') or r.get('IP') or '').strip()
        if not code:
            continue
        rows.append({'id':code,'code':code,'name':(r.get('Name') or '').strip(),'phone':(r.get('Phone') or '').strip(),'address':(r.get('Address') or '').strip(),'package':(r.get('Package') or '').strip(),'fee':float((r.get('Fee') or '0').strip() or 0),'pppoeUser':'','pppoePass':'','onu':'','connectionDate':(r.get('Connection Date') or '').strip(),'expiry':'','prevDue':0,'status':'active','createdAt':(r.get('Connection Date') or '').strip(),'payments':[]})
seed = json.dumps(rows, ensure_ascii=False, separators=(',',':'))
marker = '/* STAR_ACTIVE_CUSTOMER_SEED_V1 */'
if marker not in text:
    js = f'''<script>{marker}\n(function(){{\nconst STAR_ACTIVE_SEED={seed};\nconst STAR_ACTIVE_SEED_KEY='star_active_customer_seed_v1';\nfunction seedActiveCustomers(){{try{{if(localStorage.getItem(STAR_ACTIVE_SEED_KEY)==='1')return;d.customers=STAR_ACTIVE_SEED.map(x=>JSON.parse(JSON.stringify(x)));if(typeof save==='function')save();localStorage.setItem(STAR_ACTIVE_SEED_KEY,'1');}}catch(e){{console.error(e);}}}}\nif(typeof fix==='function'){{const oldFix=fix;fix=function(){{seedActiveCustomers();oldFix();}};}}else seedActiveCustomers();\n}})();\n</script>'''
    text = text.replace('</body>', js + '</body>')
    HTML.write_text(text, encoding='utf-8')
print(f'Embedded {len(rows)} active customers into APK seed.')
