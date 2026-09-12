from pathlib import Path
import re

p=Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
s=p.read_text(encoding='utf-8')

# Remove Android-side dashboard injection that was bringing back Total Left Client/Package.
s,n=re.subn(r'"var oldDash=window\.dashboard;window\.dashboard=function\(\)\{.*?;\};"\+\n', '', s, count=1, flags=re.S)
print('Removed old dashboard injection:', n)

# Remove Android-side Add Customer override so the HTML Customers page is the only source of the form.
s,n=re.subn(r'"var oldAdd=window\.addCustomer;window\.addCustomer=function\(\)\{.*?;\};"\+\n', '', s, count=1, flags=re.S)
print('Removed old Add Customer override:', n)

# Replace the old wrapper with a reliable native-side JS save implementation.
old_pattern=r'"var oldSave=window\.saveCustomer;window\.saveCustomer=function\(\)\{.*?\};"\+\n'
new='''"window.saveCustomer=function(){try{var name=(document.getElementById('n')||{}).value.trim(),code=((document.getElementById('cc')||{}).value||'').trim().toUpperCase(),phone=(document.getElementById('p')||{}).value.trim(),address=(document.getElementById('a')||{}).value.trim(),pkg=(document.getElementById('pkg')||{}).value||'',fee=Number((document.getElementById('fee')||{}).value||0),pp=(document.getElementById('pp')||{}).value.trim(),pw=(document.getElementById('pw')||{}).value,onu=(document.getElementById('onu')||{}).value.trim(),cd=(document.getElementById('cd')||{}).value||today(),ex=(document.getElementById('ex')||{}).value||'',prev=Number((document.getElementById('prev')||{}).value||0);if(!name){toast('Customer name required');return;}if(!code)code='SC'+String((d.customers||[]).length+1).padStart(3,'0');if((d.customers||[]).some(function(x){return String(x.clientCode||'').toUpperCase()===code;})){toast('Client Code already exists');return;}var c={id:Date.now().toString(),clientCode:code,name:name,phone:phone,address:address,pkg:pkg,fee:fee,pppoeUser:pp,pppoePass:pw,onu:onu,connectionDate:cd,expiry:ex,prevDue:prev,status:'active',createdAt:today()};d.customers=d.customers||[];d.customers.push(c);localStorage.setItem(KEY,JSON.stringify(d));try{localStorage.setItem(KEY+'_backup',JSON.stringify(d));}catch(e){}try{if(window.AndroidBridge){if(c.expiry)AndroidBridge.scheduleExpiry(String(c.phone),String(c.name),String(c.expiry));if(c.phone)AndroidBridge.scheduleMonthEnd(String(c.phone),String(c.name));}}catch(e){}closeSheet();toast('Customer Saved');go('customers',{filter:'all'},false);}catch(e){toast('Save failed: '+e.message);}};"+\n'''
s,n=re.subn(old_pattern,new,s,count=1,flags=re.S)
print('Replaced saveCustomer:', n)

# After every render: remove duplicate Add Customer controls outside the Customers page.
needle='"try{render();}catch(e){}})();";'
replacement='''"try{render();}catch(e){};function cleanAddButtons(){try{document.querySelectorAll('button,.stat,.section').forEach(function(el){var t=(el.textContent||'').trim();if(t.indexOf('Add Customer')>=0&&t.indexOf('Add New Customer')<0&&el.closest('#modal')===null)el.remove();});if(page==='dashboard'){var c=document.getElementById('content');if(c&&!c.querySelector('[data-star-add-new]')){var x=document.createElement('div');x.className='stat blue';x.setAttribute('data-star-add-new','1');x.style.margin='8px 0';x.innerHTML='<div class=label>＋ Add New Customer</div><div class=num>Customer</div>';x.onclick=function(){go('customers',{filter:'all'});setTimeout(function(){addCustomer();},50)};c.appendChild(x);}}}catch(e){}};var oldRender=window.render;window.render=function(){oldRender();setTimeout(cleanAddButtons,0);};cleanAddButtons();";'''
if needle in s:
    s=s.replace(needle,replacement,1)
else:
    print('Render hook needle not found; continuing')

p.write_text(s,encoding='utf-8')
