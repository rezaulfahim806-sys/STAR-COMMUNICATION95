from pathlib import Path

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')

marker="function totalUnpaid(){return d.customers.filter(c=>due(c)>0).reduce((a,c)=>a+due(c),0)}"
insert="function monthlyBillExpectation(){return d.customers.filter(c=>c.status==='active').reduce((a,c)=>a+Number(c.fee||0),0)}function currentMonthUnpaid(){return Math.max(0,monthlyBillExpectation()-totalPaid())}function collectionPercent(){let e=monthlyBillExpectation();return e>0?Math.min(100,Math.round(totalPaid()/e*100)):0}function nextMonthExpected(){return monthlyBillExpectation()}"
if 'function monthlyBillExpectation()' not in s:
    if marker not in s:
        raise SystemExit('billing marker not found')
    s=s.replace(marker,marker+insert,1)

old='<div class="chart"><b>🏢 Company Growth</b>${bars(companyGrowth())}</div>'
new=old+'<div class="section"><h3>📅 Monthly Bill Expectation</h3><div class="moneygrid"><div class="moneybox"><span class="muted">Expected</span><b>${money(monthlyBillExpectation())}</b></div><div class="moneybox"><span class="muted">Collected</span><b class="success">${money(totalPaid())}</b></div><div class="moneybox"><span class="muted">Unpaid</span><b class="danger">${money(currentMonthUnpaid())}</b></div></div><div class="kpi"><span>Collection</span><b>${collectionPercent()}%</b></div><div class="kpi"><span>Next Month Expected</span><b>${money(nextMonthExpected())}</b></div></div>'
if '📅 Monthly Bill Expectation' not in s:
    if old not in s:
        raise SystemExit('company growth dashboard marker not found')
    s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('growth expectation patch applied')
