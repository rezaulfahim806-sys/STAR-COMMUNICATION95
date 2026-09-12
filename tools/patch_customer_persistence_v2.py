from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
# Make customer storage durable across app restarts/reloads.
if "function save(){const j=JSON.stringify(d);" not in s:
    old="function save(){localStorage.setItem(KEY,JSON.stringify(d))}"
    new="function save(){const j=JSON.stringify(d);try{localStorage.setItem(KEY,j);localStorage.setItem(KEY+'_backup',j)}catch(e){try{localStorage.setItem(KEY+'_backup',j)}catch(_){} }}"
    s=s.replace(old,new,1)
old2="let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d)d=JSON.parse(JSON.stringify(DEF));"
new2="let d;try{d=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){d=null}if(!d){try{d=JSON.parse(localStorage.getItem(KEY+'_backup')||'null')}catch(e){d=null}}if(!d)d=JSON.parse(JSON.stringify(DEF));"
if old2 in s:s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
