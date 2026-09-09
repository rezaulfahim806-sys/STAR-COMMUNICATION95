# STAR COMMUNICATION — Live APK + Backend

Upload the project contents to the ROOT of a GitHub repository.

Root files should include:
- `settings.gradle`
- `build.gradle`
- `gradle.properties`
- `package.json`
- `server.js`
- `.env.example`
- `app/build.gradle`
- `app/src/main/AndroidManifest.xml`
- `app/src/main/assets/index.html`
- `app/src/main/java/com/starcommunication/isp/MainActivity.java`
- `.github/workflows/build-apk.yml`

## APK
Open Actions → **Build STAR COMMUNICATION APK** → Run workflow → download `STAR-COMMUNICATION-debug-apk`.

## Backend
Deploy `server.js` as a Node service with MongoDB. Set the environment variables from `.env.example`.

## OLT live connection
The app now has a real backend OLT connection path using SSH/Telnet. Enter OLT vendor/IP/protocol/port/username and provide the password when connecting. The cloud server must be able to reach the OLT network. For private LAN OLTs, use a VPN or a local OLT agent.
