from pathlib import Path

p = Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
s = p.read_text(encoding='utf-8')

# Remove duplicate Java methods by balanced-brace scanning, keeping the first copy.
def dedupe_method(text, signature):
    positions=[]
    start=0
    while True:
        i=text.find(signature, start)
        if i<0: break
        brace=text.find('{', i)
        if brace<0: break
        depth=0; end=None
        for j in range(brace, len(text)):
            if text[j]=='{': depth+=1
            elif text[j]=='}':
                depth-=1
                if depth==0:
                    end=j+1
                    break
        if end is None: break
        positions.append((i,end))
        start=end
    if len(positions)<=1: return text,0
    removed=0
    for i,e in reversed(positions[1:]):
        text=text[:i]+text[e:]
        removed+=1
    return text,removed

s,n=dedupe_method(s,'private void requestSmsPermissions()')
print('Duplicate requestSmsPermissions removed:', n)
s,n2=dedupe_method(s,'private void requestSmsPermission()')
print('Duplicate requestSmsPermission removed:', n2)

p.write_text(s,encoding='utf-8')
