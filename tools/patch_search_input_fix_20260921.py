from pathlib import Path

html = Path('app/src/main/assets/index.html')
s = html.read_text(encoding='utf-8')

patch = r'''<script id="star-search-input-fix-20260921">
(function(){
  if(window.__starSearchInputFix20260921)return;
  window.__starSearchInputFix20260921=true;

  window.applyCustomerSearch=function(v){
    var input=document.getElementById('customerSearch');
    var start=input && typeof input.selectionStart==='number' ? input.selectionStart : String(v||'').length;
    var end=input && typeof input.selectionEnd==='number' ? input.selectionEnd : start;
    customerSearchText=String(v==null?'':v).toLowerCase();
    render();
    setTimeout(function(){
      var x=document.getElementById('customerSearch');
      if(x){
        x.focus();
        try{x.setSelectionRange(start,end)}catch(e){}
      }
    },0);
  };
})();
</script>'''

if 'id="star-search-input-fix-20260921"' not in s:
    if '</body></html>' in s:
        s=s.replace('</body></html>',patch+'</body></html>')
    else:
        s += patch
    html.write_text(s,encoding='utf-8')
