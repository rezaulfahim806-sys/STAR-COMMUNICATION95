const https = require('https');
const http = require('http');

function postJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const data = JSON.stringify(payload);
    const client = u.protocol === 'https:' ? https : http;
    const req = client.request({
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers },
      timeout: 15000
    }, res => {
      let body = '';
      res.on('data', d => body += d);
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });
    req.on('timeout', () => req.destroy(new Error('SMS provider timeout')));
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function sendPaymentSms({ mobile, customerCode, customerName, amount, transactionId }) {
  const phone = String(mobile || '').trim();
  if (!phone) return { sent: false, reason: 'customer_mobile_missing' };

  // Keep provider credentials on the backend only. Do not put them in the Android app or GitHub frontend.
  const url = process.env.SMS_API_URL;
  const apiKey = process.env.SMS_API_KEY;
  const sender = process.env.SMS_SENDER || 'STAR COMM';
  if (!url || !apiKey) return { sent: false, reason: 'sms_provider_not_configured' };

  const message = `STAR COMMUNICATION: Payment of Tk ${Number(amount || 0)} received successfully. Customer ID: ${customerCode || '-'}${transactionId ? `. Transaction ID: ${transactionId}` : ''}. Thank you.`;
  const result = await postJson(url, { api_key: apiKey, sender, to: phone, message });
  if (result.status < 200 || result.status >= 300) throw new Error(`SMS provider HTTP ${result.status}`);
  return { sent: true, mobile: phone, customerName, response: result.body.slice(0, 500) };
}

module.exports = { sendPaymentSms };
