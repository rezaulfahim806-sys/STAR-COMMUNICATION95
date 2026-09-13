from pathlib import Path

p = Path('app/src/main/java/com/starcommunication/isp/MainActivity.java')
s = p.read_text(encoding='utf-8')

# AppBridge is an inner class, so an unqualified method reference resolves against
# AppBridge. Explicitly target the enclosing MainActivity helper instead.
s = s.replace('runOnUiThread(this::requestSmsPermission);', 'runOnUiThread(MainActivity.this::requestSmsPermissions);')
s = s.replace('runOnUiThread(this::requestSmsPermissions);', 'runOnUiThread(MainActivity.this::requestSmsPermissions);')

# If the callback was emitted as a lambda, make its target explicit too.
s = s.replace('runOnUiThread(() -> requestSmsPermission());', 'runOnUiThread(() -> MainActivity.this.requestSmsPermissions());')

p.write_text(s, encoding='utf-8')
print('Fixed AppBridge SMS permission method reference.')
