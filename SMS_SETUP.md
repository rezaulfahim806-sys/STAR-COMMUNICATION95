# STAR COMMUNICATION — SMS API and Daily Expiry Reminders

## Configure the SMS provider
In the STAR COMMUNICATION app, open **Settings → SMS API Settings** and enter the provider HTTPS endpoint, API key/token, sender ID (if required), API-key field name (if the provider expects the key in its request body/query), and HTTP method. Use **Test SMS API** to confirm a test message is accepted.

Then use **Login & Sync** / Cloud Sync so the SMS settings are saved to the company's Render-backed cloud data. The scheduled job reads each company's own SMS configuration from its cloud settings. Keep credentials out of the APK, public website source, and GitHub.

The generic backend request includes these fields: `to`, `phone`, `message`, `senderid`, `senderId`, `amount`, `customerId`, and `transactionId`. For GET providers, fields are sent as query parameters; for POST, JSON is sent. If your provider needs a different field mapping or form encoding, adjust `callConfiguredApi` in `server.js`.

## Daily expiry SMS
The Render backend scheduler runs independently of the APK and website at **10:00 Bangladesh time (Asia/Dhaka)**. It checks company cloud records for customers whose expiry date is today and whose bill is still due. Each SMS includes that customer's own payment link, and a server-side log prevents duplicate sends for the same customer and expiry date.

Default template:
`STAR COMMUNICATION: Dear {name}, your internet bill expires today. Due: Tk {due}. Expiry: {expiry}. Pay here: {paymentLink}`

Supported placeholders: `{name}`, `{due}`, `{expiry}`, `{company}`, `{paymentLink}`. You can customize the expiry template in the app. Make sure the latest SMS settings and template are synced to Render.

## Payment success and dashboard
Baniq payment status is verified server-side before the bill is marked paid. The backend clears the previous due, updates the payment ledger, restores an expired customer, advances expiry by 30 days, and then attempts a payment confirmation SMS. bKash follows the same verified-payment flow. SMS provider failure does not undo a verified payment.

The app periodically syncs cloud state, so the dashboard should reflect the updated bill after the next sync. If a phone is offline, open the app and run Cloud Sync when it reconnects.

## Troubleshooting
- SMS not sent: check Settings → SMS API Settings and use **Test SMS API**.
- Settings not reaching the scheduler: log in and sync the app after saving.
- Customer not included: their expiry must be today's Bangladesh date, they must have a mobile number, and the bill must still be due; Free/Left customers are skipped.
- Delivery is not guaranteed just because the API accepted the request; check your provider's delivery report.
- See the `sms_reminder_logs` collection in MongoDB for sent/failed status. Provider credentials are never written to these logs.
