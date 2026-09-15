from pathlib import Path

p=Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
s=p.read_text(encoding='utf-8')
old='@Override public void onBackPressed(){if(webView!=null)webView.evaluateJavascript("typeof appBack===\'function\' ? appBack() : null",null);else super.onBackPressed();}'
new='@Override public void onBackPressed(){if(webView!=null){webView.evaluateJavascript("typeof appBack===\'function\' ? appBack() : null",value -> {if(webView!=null && webView.canGoBack()) webView.goBack();});}else super.onBackPressed();}'
if old in s:
    s=s.replace(old,new,1)
elif 'webView.canGoBack()' not in s:
    start=s.find('@Override public void onBackPressed()')
    if start<0: raise SystemExit('onBackPressed not found')
    end=s.find('\n',start)
    s=s[:start]+new+s[end:]
p.write_text(s,encoding='utf-8')
print('WebView back navigation patched')
