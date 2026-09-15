from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
old="""  function findCustomer(id){
    var list=(window.d&&Array.isArray(d.customers))?d.customers:[];
    var sid=String(id==null?'':id);
    return list.find(function(c){return String(c.id)===sid||String(c.clientCode||'')===sid;});
  }"""
new="""  function findCustomer(id){
    var obj=null;
    try{obj=(typeof d!=='undefined'&&d)?d:(window.d||null);}catch(e){obj=window.d||null;}
    var list=obj&&Array.isArray(obj.customers)?obj.customers:[];
    var sid=String(id==null?'':id);
    return list.find(function(c){return String(c.id)==sid||String(c.clientCode||'')==sid;});
  }"""
if old not in s: raise SystemExit('payment link function not found')
s=s.replace(old,new,1)
s=s.replace("q.set('merchant',String((d.settings&&d.settings.merchantNumber)||'01897-099850'));","q.set('merchant',String((obj&&obj.settings&&obj.settings.merchantNumber)||'01897-099850'));",1)
# Make the final link implementation work even when d is a lexical variable, not window.d.
p.write_text(s,encoding='utf-8')
print('payment link customer lookup fixed')
