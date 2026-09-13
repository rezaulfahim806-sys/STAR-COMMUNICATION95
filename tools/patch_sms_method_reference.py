from pathlib import Path

p = Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
s = p.read_text(encoding='utf-8')

# AppBridge is an inner class. Use the enclosing Activity explicitly.
s = s.replace('runOnUiThread(this::requestSmsPermission);', 'runOnUiThread(MainActivity.this::requestSmsPermission);')
s = s.replace('runOnUiThread(this::requestSmsPermissions);', 'runOnUiThread(MainActivity.this::requestSmsPermissions);')
s = s.replace('runOnUiThread(() -> requestSmsPermission());', 'runOnUiThread(() -> MainActivity.this.requestSmsPermission());')

p.write_text(s, encoding='utf-8')
print('Fixed AppBridge SMS permission method reference.')
