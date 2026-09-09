# STAR COMMUNICATION — Live Use Setup

## 1. Backend
Deploy this Node.js server on Render/Railway/VPS or another HTTPS Node host. For live mode, MongoDB and strong admin/JWT secrets are required; the server will refuse to start if they are missing.

Environment variables:
- `MONGODB_URI`
- `MONGODB_DB=star_communication`
- `JWT_SECRET` (long random secret)
- `ADMIN_USER`
- `ADMIN_PASSWORD`
- `PORT` (host may provide this automatically)

Start command: `npm start`

## 2. App login
In the APK: Menu → Server Login.
- Backend API URL: your HTTPS backend URL
- Username/password: the values configured on the backend

## 3. OLT
Settings → OLT Connection Settings.
Choose vendor, IP, SSH/Telnet and port, then username. Password is requested at connection time and is not permanently stored in the APK/localStorage.

Supported connection transports in this project: SSH and Telnet.
VSOL V1601E04-DP (EPON) is now a first-class vendor in this project. The VSOL adapter uses SSH shell login, `enable`, `configure terminal`, `show version`, and `show onu status all`; the monitor parses the EPON ONU rows into Total/Online/Offline counts and can return the live ONU table with ONU ID, status, MAC and distance. Huawei, ZTE and FiberHome presets remain available. Exact CLI output can still vary by firmware, so test against the real OLT before production.

## 4. Important
The app cannot directly reach a private OLT IP from a public cloud server unless the OLT network is reachable from that server (VPN, public/NAT route, or a local agent). For a real ISP deployment, the safest design is a small local OLT agent inside the ISP network that talks to the OLT and securely reports to the cloud backend.

Never publish the OLT password, MongoDB password, JWT secret, or bKash API credentials inside the APK or GitHub repository.
