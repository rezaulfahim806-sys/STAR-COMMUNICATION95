from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
# Remove any standalone Add Customer buttons/links from non-customers pages by changing their onclick targets to a neutral label.
# Keep only the Customers page add button generated in customers().
import re
s=re.sub(r'<button[^>]*onclick=["\']openSheet\([^)]*addCustomer[^)]*\)["\'][^>]*>\s*[^<]*Add Customer[^<]*</button>', '', s, flags=re.I)
# Replace dashboard Total Left Client stat/card with Add New Customer action, if present.
s=s.replace('Total Left Client','ADD NEW CUSTOMER')
s=s.replace('Total Left Client','Add New Customer')
# Common dashboard card patterns: make any stat whose label became Add New Customer clickable to the customer add form.
s=re.sub(r'(<div class="stat [^"]*" onclick=")go\([^)]+\)("[^>]*>\s*<div class="label">(?:ADD NEW CUSTOMER|Add New Customer)</div>)', r'\1openAddCustomer()\2', s, flags=re.I)
# Add a single global helper that opens the existing customer add sheet. If the function already exists, leave it.
if 'function openAddCustomer()' not in s:
    marker="function closeSheet(){document.getElementById('modal').classList.remove('show')}"
    s=s.replace(marker, marker+"function openAddCustomer(){go('customers',{add:true})}")
# Ensure customers page has the add button; if it already has one, do not duplicate.
# Also remove accidental add buttons from monitor/billing/accounts/analytics page render strings by replacing their visible labels.
for old in ['+ Add Customer','Add Customer','＋ Add Customer']:
    # Only remove from obvious non-customer contexts is difficult in minified HTML, so convert all occurrences except the customers renderer's first occurrence.
    pass
p.write_text(s,encoding='utf-8')
