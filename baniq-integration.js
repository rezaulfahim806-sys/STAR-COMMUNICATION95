const crypto = require('crypto');

module.exports = function registerBaniqRoutes(app, { col, ownerOf, PUBLIC_URL, PAYMENT_PAGE_URL, integrationSettings, callConfiguredApi, getBaniqCredentials, auth }) {
  const API_BASE = (process.env.BANIQ_API_BASE || 'https://api.baniq.app').replace(/\/$/, '');
  const WEBHOOK_SECRET = process.env.BANIQ_WEBHOOK_SECRET || '';

  // Keep permission parsing local to this module; Node modules do not share server.js scope.
  function packageChoiceEnabled(customer) {
    const enabled = value => value === true || ['true', '1', 'yes', 'on', 'enabled'].includes(String(value ?? '').trim().toLowerCase());
    return !!customer && (enabled(customer.allowPackageChoice) || enabled(customer.allowPackageChange));
  }

  app.get('/api/integrations/baniq/health', auth, async (req,res) => {
    try {
      const credentials = await getBaniqCredentials(req.user && req.user.owner || req.user && req.user.username || '');
      const configured = !!(credentials.keyId && credentials.secret);
      const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 6000);
      let reachable = false, httpStatus = null;
      try {
        const response = await fetch(API_BASE + '/', { method:'GET', headers:{accept:'application/json'}, signal:controller.signal, redirect:'error' });
        reachable = true; httpStatus = response.status;
      } catch(e) {
        // Some API hosts do not serve a root page. A 404/405 still counts as reachable,
        // but DNS/TLS/network failures do not.
        reachable = false;
      } finally { clearTimeout(timer); }
      return res.json({ok:true,configured,reachable,httpStatus,apiBase:API_BASE});
    } catch(e) { return res.status(503).json({ok:false,error:String(e.message||'Baniq status check failed').slice(0,160)}); }
  });
  async function baniqFetch(owner, path, options = {}) {
    if (typeof getBaniqCredentials !== 'function') throw new Error('Company-specific Baniq settings are unavailable');
    const credentials = await getBaniqCredentials(owner);
    if (!credentials.keyId || !credentials.secret) throw new Error('This company must configure its own Baniq API Key ID and Secret in Settings');
    const response = await fetch(API_BASE + path, {
      ...options,
      headers: {
        accept: 'application/json',
        'content-type': 'application/json',
        'x-api-key-id': credentials.keyId,
        'x-api-secret': credentials.secret,
        ...(options.headers || {})
      }
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(String(data.message || data.error || 'Baniq API returned HTTP ' + response.status).slice(0, 200));
    return data;
  }
  async function findSession({ orderId, reference }) {
    const c = col('baniq_checkout_sessions');
    if (!c) throw new Error('Cloud database is not configured');
    if (orderId) return c.findOne({ orderId: String(orderId) });
    if (reference) return c.findOne({ reference: String(reference) });
    return null;
  }
  async function verifyOrder(orderId, expectedAmount, owner) {
    const data = await baniqFetch(owner, '/api/v1/orders/' + encodeURIComponent(orderId), { method: 'GET' });
    if (data.paid !== true || String(data.status || '').toLowerCase() !== 'paid') {
      return { verified: false, providerStatus: String(data.status || 'unknown') };
    }
    if (Number(data.amount) !== Number(expectedAmount)) {
      throw new Error('Verified Baniq amount does not match the expected bill');
    }
    return { verified: true, data };
  }
  async function markPaid(session, providerData) {
    const sessions = col('baniq_checkout_sessions');
    const stateCol = col('app_state');
    if (!sessions || !stateCol) throw new Error('Cloud database is not configured');
    const current = await sessions.findOne({ orderId: session.orderId });
    const state = await stateCol.findOne({ owner: session.owner });
    if (!state || !state.data) throw new Error('Company data not found after payment verification');
    const data = state.data;
    const customers = Array.isArray(data.customers) ? data.customers : [];
    const customer = customers.find(x => String(x.id) === String(session.customerCode)) || customers.find(x => String(x.clientCode || '').trim().toLowerCase() === String(session.clientCode || session.customerCode || '').trim().toLowerCase());
    if (!customer) throw new Error('Customer not found after payment verification');
    const amountTaka = Number(session.amountPaisa) / 100;
    const payments = Array.isArray(data.payments) ? data.payments : (data.payments = []);
    const alreadyAdded = payments.some(p => String(p.baniqOrderId || '') === String(session.orderId));
    const now = new Date().toISOString();
    const paidAt = providerData.paidAt || providerData.paid_at || providerData.completedAt || providerData.completed_at || now;
    const trxIdValue = providerData.trxId || providerData.trxID || providerData.trx_id || providerData.transactionId || providerData.transactionID || providerData.transaction_id || providerData.paymentReference || providerData.payment_reference || '';
    const trxId = String(trxIdValue || '').trim();
    customer.pkg = session.selectedPackage;
    customer.fee = Number(session.packagePrice);
    customer.prevDue = 0;
    // A verified full bill payment must immediately restore service for expired/unpaid customers.
    customer.status = 'active';
    customer.left = false;
    customer.disconnected = false;
    const nextExpiry = new Date();
    nextExpiry.setDate(nextExpiry.getDate() + 30);
    customer.expiry = nextExpiry.toISOString().slice(0, 10);
    customer.clientCode = String(session.clientCode || customer.clientCode || session.customerCode).replace(/\s+/g, '').toUpperCase();
    const canonicalCustomerId = String(customer.id || session.customerCode);
    customer.lastPaymentStatus = 'paid';
    customer.lastPaymentMonth = now.slice(0, 7);
    customer.lastPaymentAmount = amountTaka;
    customer.lastPaymentSource = 'baniq';
    customer.lastPaymentAt = now;
    customer.updatedAt = now;
    if (!alreadyAdded) {
      payments.push({
        id: 'baniq-' + session.orderId,
        customer: canonicalCustomerId,
        clientCode: String(session.clientCode || customer.clientCode || session.customerCode),
        customerName: String(customer.name || session.customerName || 'Customer'),
        amount: amountTaka,
        date: now.slice(0, 10),
        month: now.slice(0, 7),
        status: 'paid',
        source: 'baniq',
        ref: String(providerData.reference || session.reference),
        trxId: trxId || undefined,
        baniqOrderId: String(session.orderId),
        createdAt: now,
        paidAt: String(paidAt),
        verifiedAt: now,
        updatedAt: now
      });
    }
    await stateCol.updateOne({ owner: session.owner }, { $set: { data, updatedAt: now } });
    await sessions.updateOne({ orderId: session.orderId }, { $set: {
      status: 'PAID',
      verifiedAmountPaisa: Number(providerData.amount),
      paidAt: String(paidAt),
      trxId: trxId || undefined,
      verifiedAt: now,
      updatedAt: now
    } });
    // Send a payment receipt only after the verified bill is saved. SMS failure must not undo a verified payment.
    try {
      const latestSession = await sessions.findOne({ orderId: session.orderId });
      if (latestSession && !latestSession.receiptSmsSentAt && typeof integrationSettings === 'function' && typeof callConfiguredApi === 'function') {
        const settings = await integrationSettings(session.owner);
        const sms = settings.smsApi || {};
        const phone = String(session.customerMobile || customer.mobile || customer.phone || '').trim();
        if (sms.url && sms.apiKey && phone) {
          const message = 'STAR COMMUNICATION: Dear ' + String(customer.name || session.customerName || 'Customer') +
            ', your payment of Tk ' + amountTaka.toFixed(2) + ' has been verified successfully. Client Code: ' +
            String(customer.clientCode || session.clientCode || '') + '. Your bill is PAID. Thank you.';
          await callConfiguredApi({ ...sms, apiKeyField: sms.apiKeyField, senderId: sms.senderId }, { phone, message, amount: amountTaka, customerId: canonicalCustomerId, transactionId: String(providerData.reference || session.reference || session.orderId) });
          await sessions.updateOne({ orderId: session.orderId, receiptSmsSentAt: { $exists: false } }, { $set: { receiptSmsSentAt: new Date().toISOString(), receiptSmsStatus: 'accepted' } });
        } else {
          await sessions.updateOne({ orderId: session.orderId, receiptSmsStatus: { $exists: false } }, { $set: { receiptSmsStatus: 'not_configured_or_no_phone' } });
        }
      }
    } catch (smsError) {
      await sessions.updateOne({ orderId: session.orderId }, { $set: { receiptSmsStatus: 'failed', receiptSmsError: String(smsError.message || 'SMS failed').slice(0, 180) } }).catch(() => {});
    }
    return { ...session, status: 'PAID', clientCode: String(customer.clientCode || session.clientCode || '') };
  }

  app.post('/api/baniq/create', async (req, res) => {
    try {
      const body = req.body || {};
      const owner = String(body.company || '').trim().toLowerCase();
      let customerCode = String(body.customerCode || '').trim();
      const requestedClientCode = String(body.clientCode || '').trim();
      let selectedPackage = String(body.selectedPackage || '').trim();
      let packagePrice = Number(body.packagePrice || 0);
      let requestedAmount = Number(body.amount || 0);
      if (!owner || !customerCode || !selectedPackage || !Number.isFinite(packagePrice) || packagePrice <= 0) {
        return res.status(400).json({ error: 'Company, customer and selected package are required' });
      }
      const stateCol = col('app_state');
      if (!stateCol) return res.status(503).json({ error: 'Cloud database is not configured' });
      const state = await stateCol.findOne({ owner });
      if (!state || !state.data) return res.status(404).json({ error: 'Company cloud data was not found' });
      const companyCustomers = Array.isArray(state.data.customers) ? state.data.customers : [];
      const customer = companyCustomers.find(c => String(c.id) === customerCode) || companyCustomers.find(c => requestedClientCode && String(c.clientCode || '').trim().toLowerCase() === requestedClientCode.toLowerCase());
      if (!customer) return res.status(404).json({ error: 'Customer does not belong to this company. Please sync this customer to the same company account and retry.' });
      // Store the company's canonical customer ID and a stable human-readable client code.
      customerCode = String(customer.id || customerCode);
      const normalizeClientCode = value => String(value || '').replace(/\s+/g, '').trim().toUpperCase();
      let clientCode = normalizeClientCode(customer.clientCode || requestedClientCode);
      if (!/^SC\d{3,}$/i.test(clientCode)) {
        const used = new Set(companyCustomers.map(c => {
          const m = normalizeClientCode(c.clientCode).match(/^SC0*(\d+)$/i);
          return m ? Number(m[1]) : 0;
        }));
        let n = 1;
        while (used.has(n)) n++;
        clientCode = 'SC' + String(n).padStart(3, '0');
        customer.clientCode = clientCode;
        customer.updatedAt = new Date().toISOString();
        await stateCol.updateOne({ owner }, { $set: { data: state.data, updatedAt: customer.updatedAt } });
      } else {
        customer.clientCode = clientCode;
      }
      const packages = Array.isArray(state.data.settings && state.data.settings.packages) ? state.data.settings.packages : [];
      // If package choice is enabled, the customer may only pay for a current company package.
      // If it is disabled, honor the package and fee already assigned to this customer even if
      // the company has since removed/renamed that package in Settings.
      const enabledFlag = value => value === true || ['true', '1', 'yes', 'on', 'enabled'].includes(String(value ?? '').trim().toLowerCase());
      const packageChoiceAllowed = packageChoiceEnabled(customer);
      if (packageChoiceAllowed) {
        // Normalize legacy/current package records consistently (speed/name and price/fee),
        // so harmless casing/spacing or numeric-string differences do not reject a valid choice.
        const normalizePackageName = value => String(value || '').trim().replace(/\s+/g, ' ').replace(/\s*mbps\s*$/i, '').trim().toLocaleLowerCase();
        const livePackage = packages.find(p =>
          normalizePackageName(p && (p.speed || p.name)) === normalizePackageName(selectedPackage)
        );
        if (!livePackage) {
          return res.status(409).json({ error: 'This package is not published in this company account. Open Admin > Settings > Manage Payment Packages, publish the package list, then create a new payment link.' });
        }
        // Use the current cloud package price as the source of truth. A stale payment link
        // must not fail checkout solely because its embedded price is old, and clients
        // must never be able to submit an arbitrary amount.
        selectedPackage = String(livePackage.speed || livePackage.name).trim();
        packagePrice = Number(livePackage.price ?? livePackage.fee ?? 0);
        if (!selectedPackage || !Number.isFinite(packagePrice) || packagePrice <= 0) {
          return res.status(409).json({ error: 'The selected company package has an invalid price. Update the package in Admin Settings.' });
        }
      } else {
        // OFF means the customer cannot choose a package: use the saved assignment as the
        // source of truth instead of rejecting checkout because an old link has stale labels/prices.
        const currentSpeed = String(customer.pkg || customer.packageName || customer.package || '').trim();
        const currentPrice = Number(customer.fee ?? customer.monthlyFee ?? customer.price ?? 0);
        if (!currentSpeed || !Number.isFinite(currentPrice) || currentPrice <= 0) {
          return res.status(409).json({ error: 'This customer has no valid assigned package or monthly bill. Update the customer record first.' });
        }
        selectedPackage = currentSpeed;
        packagePrice = currentPrice;
      }
      const previousDue = Math.max(0, Number(customer.prevDue ?? customer.previousDue ?? 0));
      const amountTaka = Number((packagePrice + previousDue).toFixed(2));
      // For locked customers, ignore the stale amount embedded in an older payment link.
      // The checkout amount is always recalculated from the saved package and previous due.
      if (packageChoiceAllowed && (!Number.isFinite(requestedAmount) || Math.abs(requestedAmount - amountTaka) > 0.01)) {
        return res.status(409).json({ error: 'Payment amount does not match the selected package and previous due' });
      }
      requestedAmount = amountTaka;
      const reference = ('SC-' + clientCode.replace(/\s+/g, '-') + '-' + Date.now()).replace(/[^A-Za-z0-9_-]/g, '').slice(0, 80);
      const amountPaisa = Math.round(amountTaka * 100);
      const callback = PUBLIC_URL + '/api/baniq/callback?reference=' + encodeURIComponent(reference);
      const created = await baniqFetch(owner, '/api/v1/orders', {
        method: 'POST',
        body: JSON.stringify({
          amount: amountPaisa,
          productName: 'STAR COMMUNICATION ' + clientCode + ' - ' + String(customer.name || body.customerName || 'Customer') + ' Internet Bill - ' + selectedPackage,
          reference,
          successUrl: callback,
          cancelUrl: PAYMENT_PAGE_URL + '?status=cancelled&api=' + encodeURIComponent(PUBLIC_URL),
          customerName: clientCode + ' - ' + String(customer.name || body.customerName || 'Customer'),
          customerPhone: String(customer.mobile || customer.phone || body.customerMobile || ''),
          metadata: { company: owner, customerCode, clientCode, customerName: String(customer.name || body.customerName || 'Customer'), selectedPackage, packagePrice, previousDue, orderType: 'isp-bill' }
        })
      });
      if (!created.orderId || !created.checkoutUrl) throw new Error('Baniq did not return a checkout URL');
      const sessions = col('baniq_checkout_sessions');
      await sessions.insertOne({
        orderId: String(created.orderId), reference, owner, customerCode, clientCode,
        customerName: String(customer.name || body.customerName || 'Customer'),
        customerMobile: String(customer.mobile || customer.phone || body.customerMobile || ''),
        selectedPackage, packagePrice, previousDue, amountPaisa,
        status: 'PENDING', createdAt: new Date().toISOString()
      });
      return res.json({ ok: true, orderId: String(created.orderId), checkoutUrl: created.checkoutUrl, reference });
    } catch (e) {
      return res.status(502).json({ error: String(e.message || 'Unable to start Baniq payment').slice(0, 220) });
    }
  });

  app.get('/api/baniq/status', async (req, res) => {
    try {
      const orderId = String(req.query.orderId || '').trim();
      if (!orderId) return res.status(400).json({ error: 'orderId is required' });
      const session = await findSession({ orderId });
      if (!session) return res.status(404).json({ ok: true, verified: false, status: 'NOT_FOUND' });
      if (session.status === 'PAID') {
        await markPaid(session, { amount: Number(session.verifiedAmountPaisa || session.amountPaisa), reference: session.reference, paidAt: session.paidAt });
        const state = await col('app_state').findOne({ owner: session.owner }); const customers = Array.isArray(state?.data?.customers) ? state.data.customers : []; const customer = customers.find(x => String(x.id) === String(session.customerCode)) || customers.find(x => String(x.clientCode || '').toLowerCase() === String(session.clientCode || '').toLowerCase()); return res.json({ ok: true, verified: true, status: 'PAID', customerCode: customer?.id || session.customerCode, clientCode: String(customer?.clientCode || session.clientCode || ''), customerName: customer?.name || session.customerName || '', orderId });
      }
      const verification = await verifyOrder(orderId, session.amountPaisa, session.owner);
      if (!verification.verified) return res.json({ ok: true, verified: false, status: verification.providerStatus, customerCode: session.customerCode, orderId });
      const paid = await markPaid(session, verification.data);
      return res.json({ ok: true, verified: true, status: paid.status, customerCode: session.customerCode, clientCode: String(paid.clientCode || session.clientCode || ''), customerName: session.customerName || '', orderId });
    } catch (e) {
      return res.status(502).json({ ok: false, verified: false, error: String(e.message || 'Baniq verification failed').slice(0, 200) });
    }
  });

  app.get('/api/baniq/callback', async (req, res) => {
    const reference = String(req.query.reference || '').trim();
    const orderIdFromQuery = String(req.query.orderId || req.query.oid || '').trim();
    const page = (status, orderId = '') => {
      const params = new URLSearchParams({ status, api: PUBLIC_URL });
      if (orderId) params.set('orderId', orderId);
      if (reference) params.set('reference', reference);
      return res.redirect(PAYMENT_PAGE_URL + '?' + params.toString());
    };
    try {
      const session = await findSession({ orderId: orderIdFromQuery, reference });
      if (!session) return page('failed');
      const result = await verifyOrder(session.orderId, session.amountPaisa, session.owner);
      if (!result.verified) return page('pending', session.orderId);
      await markPaid(session, result.data);
      return page('success', session.orderId);
    } catch (e) {
      return page('pending', orderIdFromQuery);
    }
  });

  app.post('/api/baniq/webhook', async (req, res) => {
    try {
      if (!WEBHOOK_SECRET) return res.status(503).json({ error: 'Baniq webhook secret is not configured' });
      const signature = String(req.get('x-deshpay-signature') || '');
      const rawBody = req.rawBody;
      if (!rawBody) return res.status(400).json({ error: 'Raw webhook body unavailable' });
      const expected = 'sha256=' + crypto.createHmac('sha256', WEBHOOK_SECRET).update(rawBody).digest('hex');
      const a = Buffer.from(signature), b = Buffer.from(expected);
      if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return res.status(401).json({ error: 'Invalid Baniq webhook signature' });
      const payload = JSON.parse(rawBody.toString('utf8'));
      if (payload.event !== 'order.paid' || !payload.order) return res.status(200).json({ ok: true, ignored: true });
      const order = payload.order;
      const session = await findSession({ orderId: String(order.id || '') , reference: String(order.reference || '') });
      if (!session) return res.status(200).json({ ok: true, ignored: true, reason: 'No matching payment session' });
      if (Number(order.amount) !== Number(session.amountPaisa) || String(order.status || '').toLowerCase() !== 'paid') {
        return res.status(409).json({ error: 'Webhook order does not match expected payment' });
      }
      await markPaid(session, order);
      return res.status(200).json({ ok: true });
    } catch (e) {
      return res.status(400).json({ error: String(e.message || 'Invalid Baniq webhook').slice(0, 180) });
    }
  });
};
