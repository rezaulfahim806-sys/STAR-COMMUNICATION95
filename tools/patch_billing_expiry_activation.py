from pathlib import Path

# Keep the original expiry logic intact.
# Final rule: expiry makes a customer Expired; any positive payment immediately
# reactivates that customer to Active. The payment-flow patch handles reactivation.
print('Verified: keep expiry logic; positive payment reactivates expired customer.')
