from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
# Remove common non-customer-page add-customer controls while preserving the dedicated Customers page button.
# Dashboard should use the dedicated new-customer action instead of a client-count card.
s=s.replace('Total Left Client','Add New Customer')
# Any dashboard stat with this label becomes an add action.
s=s.replace('onclick="go(\'customers\',{filter:\'left\'})"','onclick="openAddCustomer()"')
# Ensure helper exists.
if 'function openAddCustomer()' not in s:
    s=s.replace("function closeSheet(){document.getElementById('modal').classList.remove('show')}","function closeSheet(){document.getElementById('modal').classList.remove('show')}function openAddCustomer(){go('customers',{add:true})}")
p.write_text(s,encoding='utf-8')
