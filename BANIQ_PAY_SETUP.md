# Baniq Pay integration for STAR COMMUNICATION

This branch adds Baniq Pay checkout to the existing customer bill-payment page. Existing customer package selection and the owner package editor remain in place.

## Required Render environment variables

Set these on the existing backend service in Render (Environment):

- `BANIQ_API_BASE=https://api.baniq.app`
- `BANIQ_KEY_ID=dpk_...`
- `BANIQ_SECRET=dps_...`
- `BANIQ_WEBHOOK_SECRET=...`
- `PUBLIC_URL=https://YOUR-BACKEND-DOMAIN`
- `PAYMENT_PAGE_URL=https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html`

Use the real values from your Baniq dashboard. Never put the API secret or webhook secret in the browser, APK, GitHub source, or a public screenshot.

## Baniq dashboard

In Baniq Dashboard → API & Webhook:

- Add webhook URL: `https://YOUR-BACKEND-DOMAIN/api/baniq/webhook`
- Set the same webhook secret as `BANIQ_WEBHOOK_SECRET`.
- Enable the `order.paid` event.

## What happens

1. The customer selects one of the company's current packages in `pay.html`.
2. The backend independently checks the customer, package price, and due amount against the company's cloud data.
3. The backend creates a Baniq order and redirects the customer to Baniq's hosted checkout.
4. The callback and signed webhook are verified server-side. The backend also supports checking the order directly through Baniq's verify API.
5. Only a verified, matching amount marks the customer bill paid. Duplicate webhook/callback processing does not add a duplicate payment.

## Package management

The existing owner settings page manages packages and publishes them to customer payment links. The backend now accepts up to 1,000 packages per company instead of 100. Package names and prices are still validated server-side.

## Before going live

- Add the Render environment variables and deploy this branch.
- Set the Baniq webhook URL and secret.
- Test with a small permitted payment and confirm the order appears as paid in Baniq and in STAR COMMUNICATION.
- Do not treat a browser redirect by itself as proof of payment.
