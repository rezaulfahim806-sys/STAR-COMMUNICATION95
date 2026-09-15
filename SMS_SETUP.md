# STAR COMMUNICATION — Payment SMS

The backend now includes `sms-notifier.js` for customer payment confirmation SMS.

## Environment variables
Set these on the backend hosting service (Render/Railway/etc.), never inside the Android app or `pay.html`:

- `SMS_API_URL` — your SMS provider's HTTPS JSON endpoint
- `SMS_API_KEY` — provider API key/token
- `SMS_SENDER` — approved sender ID (default: `STAR COMM`)

## Payload sent to the provider
```json
{
  "api_key": "SERVER_SIDE_SECRET",
  "sender": "STAR COMM",
  "to": "CUSTOMER_MOBILE",
  "message": "STAR COMMUNICATION: Payment of Tk 500 received successfully. Customer ID: SC002. Transaction ID: TX123. Thank you."
}
```

## Important
The SMS is intended to be triggered only after the backend has verified a successful payment. Do not trigger it from the browser just because a payment button was clicked.

A real SMS cannot be sent until an SMS provider account/API is configured. The repository does not contain or expose any provider secret.
