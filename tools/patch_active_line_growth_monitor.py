from pathlib import Path

p = Path('app/src/main/assets/index.html')
s = p.read_text(encoding='utf-8')

css = '<style id="active-line-growth-monitor-css">.quickgrid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:8px 0}.quickcard{background:#fff;border-radius:14px;padding:11px;box-shadow:0 3px 12px #0000000a;cursor:pointer;border:1px solid #edf0f4}.quickcard b{display:block}.quicknum{font-size:21px;font-weight:900;margin-top:5px}.quickgreen{color:#119b50}.quickblue{color:#1677d2}.quickpurple{color:#7656d6}.quickfull{grid-column:1/-1}.livepill{display:inline-block;margin-top:5px;padding:4px 7px;border-radius:12px;background:#dcfce7;color:#15803d;font-size:9px;font-weight:900}</style>'
if 'active-line-growth-monitor-css' not in s:
    s = s.replace('</head>', css + '</head>', 1)

js = r'''<script id="active-line-growth-monitor-script">
(function(){
  function addQuickPanel(){
    if(typeof page==='undefined' || page!=='dashboard') return;
    const content=document.getElementById('content');
    if(!content || document.getElementById('active-line-growth-monitor')) return;
    const customers=d.customers||[];
    const active=customers.filter(c=>c.status==='active').length;
    const inactive=customers.filter(c=>c.status==='inactive').length;
    const expired=customers.filter(c=>c.status==='expired').length;
    const ym=month();
    const newThis=customers.filter(c=>String(c.createdAt||c.connectionDate||'').slice(0,7)===ym).length;
    const prev=new Date();
    prev.setMonth(prev.getMonth()-1);
    const pm=prev.getFullYear()+'-'+String(prev.getMonth()+1).padStart(2,'0');
    const newPrev=customers.filter(c=>String(c.createdAt||c.connectionDate||'').slice(0,7)===pm).length;
    const growth=newPrev>0?Math.round((newThis-newPrev)/newPrev*100):(newThis>0?100:0);
    const box=document.createElement('div');
    box.id='active-line-growth-monitor';
    box.className='quickgrid';
    box.innerHTML=`<div class="quickcard" onclick="go('customers',{filter:'active'})"><span class="muted">📡 Active Line</span><div class="quicknum quickgreen">${active}</div><span class="muted">Active customer lines</span></div><div class="quickcard" onclick="go('analytics')"><span class="muted">📈 Growth</span><div class="quicknum quickpurple">${growth>=0?'+':''}${growth}%</div><span class="muted">${newThis} new this month</span></div><div class="quickcard quickfull" onclick="go('monitor')"><span class="muted">🔴 Live Monitoring</span><div style="display:flex;justify-content:space-between;align-items:end;gap:8px"><div><div class="quicknum quickblue">${active}</div><span class="muted">Active • ${inactive} inactive • ${expired} expired</span></div><span class="livepill">OPEN MONITOR</span></div></div>`;
    const grid=content.querySelector('.grid');
    if(grid && grid.parentNode) grid.parentNode.insertBefore(box,grid.nextSibling);
    else content.appendChild(box);
  }
  setTimeout(addQuickPanel,300);
  setInterval(addQuickPanel,1000);
})();
</script>'''

if 'active-line-growth-monitor-script' not in s:
    s = s.replace('</body>', js + '</body>', 1)

p.write_text(s, encoding='utf-8')
print('Fixed Active Line, Growth and Live Monitoring dashboard panel injection.')
