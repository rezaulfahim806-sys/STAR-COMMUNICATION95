// Server-side daily expiry SMS scheduler for STAR COMMUNICATION.
// Runs independently of the APK/browser; credentials remain in company cloud settings.
module.exports = function startScheduledExpirySms({ col, integrationSettings, callConfiguredApi, paymentPageUrl, publicUrl }) {
  let running = false;
  const timezone = 'Asia/Dhaka';

  function localParts(date) {
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
    }).formatToParts(date);
    const out = {};
    for (const p of parts) if (p.type !== 'literal') out[p.type] = p.value;
    return out;
  }
  function enabled(value) {
    return value === true || ['true', '1', 'yes', 'on', 'enabled'].includes(String(value ?? '').trim().toLowerCase());
  }
  function dateKey(value) {
    const s = String(value || '').trim();
    const m = s.match(/^(\d{4}-\d{2}-\d{2})/);
    return m ? m[1] : '';
  }
  function dueFor(customer, data, month) {
    if (customer.free || customer.status === 'left') return 0;
    if (Array.isArray(customer.freeBillMonths) && customer.freeBillMonths.includes(month)) {
      return Math.max(0, Number(customer.prevDue || 0));
    }
    const paid = (Array.isArray(data.payments) ? data.payments : []).filter(p =>
      String(p.customer) === String(customer.id) && String(p.month || '') === month &&
      String(p.status || '').toLowerCase() === 'paid'
    ).reduce((sum, p) => sum + Number(p.amount || 0), 0);
    return Math.max(0, Number(customer.prevDue || 0) + Math.max(0, Number(customer.fee || 0) - paid));
  }
  function paymentLink(owner, customer, data, due, day) {
    const base = String(paymentPageUrl || 'https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html');
    const settings = data.settings || {};
    const packages = Array.isArray(settings.packages) ? settings.packages : [];
    const allowChoice = enabled(customer.allowPackageChoice) || enabled(customer.allowPackageChange);
    const visiblePackages = (allowChoice && packages.length ? packages : [{ speed: String(customer.pkg || ''), price: Number(customer.fee || 0) }])
      .filter(p => p && String(p.speed || p.name || '').trim() && Number(p.price ?? p.fee ?? 0) > 0)
      .map(p => ({ speed: String(p.speed || p.name), price: Number(p.price ?? p.fee) }));
    const q = new URLSearchParams({
      code: String(customer.id || ''),
      clientCode: String(customer.clientCode || customer.code || ''),
      company: String(owner || '').trim().toLowerCase(),
      mobile: String(customer.phone || customer.mobile || ''),
      name: String(customer.name || 'Customer'),
      location: String(customer.address || ''),
      package: String(customer.pkg || ''),
      bill: String(customer.fee || 0),
      prev: String(customer.prevDue || 0),
      total: String(due),
      merchant: String(settings.merchantNumber || ''),
      allowPackageChoice: String(allowChoice),
      packages: JSON.stringify(visiblePackages),
      api: String(publicUrl || 'https://star-communication-api.onrender.com'),
      v: 'daily-expiry-sms'
    });
    return base + '?' + q.toString();
  }
  async function run() {
    if (running) return;
    running = true;
    try {
      const now = new Date();
      const parts = localParts(now);
      const day = parts.year + '-' + parts.month + '-' + parts.day;
      // Run at/after 10:00 Bangladesh time. Per-customer logs prevent duplicates across restarts.
      if (Number(parts.hour) < 10) return;
      const stateCollection = col('app_state');
      const logCollection = col('sms_reminder_logs');
      if (!stateCollection || !logCollection) return;
      const states = await stateCollection.find({}).toArray();
      const month = day.slice(0, 7);
      for (const state of states) {
        const owner = String(state.owner || '').trim().toLowerCase();
        const data = state.data || {};
        const settings = data.settings || {};
        const sms = settings.smsApi || {};
        if (!owner || !sms.url || !sms.apiKey) continue;
        const customers = Array.isArray(data.customers) ? data.customers : [];
        for (const customer of customers) {
          const phone = String(customer.phone || customer.mobile || '').trim();
          if (!phone || customer.free || ['left', 'inactive', 'disconnected', 'off'].includes(String(customer.status || '').toLowerCase()) || dateKey(customer.expiry) !== day) continue;
          const due = dueFor(customer, data, month);
          if (!(due > 0)) continue;

          const key = owner + '|' + String(customer.id || customer.clientCode || phone) + '|' + day;
          try {
            await logCollection.insertOne({
              _id: key, owner, customerId: String(customer.id || ''),
              phone, expiryDate: day, status: 'sending', createdAt: new Date().toISOString()
            });
          } catch (e) {
            if (e && e.code === 11000) continue;
            throw e;
          }

          try {
            const link = paymentLink(owner, customer, data, due, day);
            const template = String(settings.expirySmsTemplate || settings.smsTemplate ||
              'STAR COMMUNICATION: Dear {name}, your internet bill expires today. Due: Tk {due}. Expiry: {expiry}. Pay here: {paymentLink}');
            let message = template
              .replaceAll('{name}', String(customer.name || 'Customer'))
              .replaceAll('{due}', String(due))
              .replaceAll('{expiry}', String(customer.expiry || day))
              .replaceAll('{company}', String(settings.cloud && settings.cloud.companyName || 'STAR COMMUNICATION'))
              .replaceAll('{paymentLink}', link);
            if (!message.includes(link)) message += ' Payment link: ' + link;
            const result = await callConfiguredApi({ ...sms, apiKeyField: sms.apiKeyField, senderId: sms.senderId }, {
              phone, message, customerId: String(customer.id || ''), amount: due
            });
            const response = JSON.stringify(result && result.data || {}).slice(0, 500);
            await logCollection.updateOne({ _id: key }, { $set: {
              status: 'sent', sentAt: new Date().toISOString(), providerResponse: response
            } });
            console.log('[expiry-sms] accepted for owner=' + owner + ' customer=' + String(customer.id || '') + ' date=' + day);
          } catch (e) {
            await logCollection.updateOne({ _id: key }, { $set: {
              status: 'failed', failedAt: new Date().toISOString(),
              error: String(e.message || 'SMS failed').slice(0, 180)
            } }).catch(() => {});
            console.error('[expiry-sms] failed for owner=' + owner + ' customer=' + String(customer.id || '') + ': ' + String(e.message || e));
          }
        }
      }
    } catch (e) {
      console.error('[expiry-sms] scheduler error:', String(e.message || e));
    } finally {
      running = false;
    }
  }
  setInterval(run, 60 * 1000);
  run();
  console.log('[expiry-sms] scheduler started (Asia/Dhaka, daily from 10:00)');
};
