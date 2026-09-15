# STAR COMMUNICATION — bKash + Automatic SMS Ready

The repository now contains the server-side flow for:

1. Customer opens the STAR COMMUNICATION payment link.
2. Payment page calls `/api/bkash/create`.
3. Backend requests a bKash Checkout payment.
4. Customer completes payment in bKash.
5. Backend executes/verifies the payment with bKash.
6. Only a verified successful payment triggers the SMS notifier.
7. SMS is sent to the customer mobile supplied by the payment link/app.
8. Customer is redirected back to the STAR COMMUNICATION payment page with the verified transaction ID.

## Required backend environment

- `BKASH_BASE_URL`
- `BKASH_APP_KEY`
- `BKASH_APP_SECRET`
- `BKASH_USERNAME`
- `BKASH_PASSWORD`
- `PUBLIC_URL`
- `PAYMENT_PAGE_URL`
- `SMS_API_URL`
- `SMS_API_KEY`
- `SMS_SENDER`

Keep all credentials only in the backend hosting service's environment variables. Never put bKash secrets or SMS API keys in Android assets, GitHub Pages, or `pay.html`.

## bKash

Use the official bKash Online Business / Payment Gateway onboarding to obtain the credentials. Start with the sandbox base URL while testing, then switch to the production base URL provided by bKash after approval.

## SMS

The repository's `sms-notifier.js` is provider-neutral. Set the provider's HTTPS JSON endpoint and API key. The exact payload may need to be adjusted to the SMS provider's documented API format.

## Important production note

The current standalone `bkash-api.js` keeps the short-lived checkout session in server memory. For a production deployment, persist payment sessions/status in MongoDB (or another durable database) so a server restart cannot lose the customer/SMS mapping. The main STAR COMMUNICATION `server.js` already has MongoDB support and should be the final production integration point.

No real payment or SMS is sent until valid bKash credentials and a real SMS provider account are configured.