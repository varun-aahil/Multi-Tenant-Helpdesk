# Quick Start Guide - Adding Data

## Current Status
✅ You have created a tenant called "Acme Corp" with schema name "acme"

## Next Steps to Add Data

### 1. Run Migrations (One-time setup)
```powershell
docker compose exec web python manage.py migrate_schemas
```

### 2. Add Domain to Hosts File (One-time setup)
1. Press `Win + R`
2. Type `notepad` and press `Ctrl+Shift+Enter` (runs as admin)
3. Click "Yes" when prompted
4. File → Open → Navigate to `C:\Windows\System32\drivers\etc\`
5. Change file type to "All Files"
6. Open `hosts`
7. Add this line at the end:
   ```
   127.0.0.1 acme.localhost
   ```
8. Save and close

### 3. Access Tenant Admin Panel
Open in browser: **http://acme.localhost:8000/admin/**

You should now see:
- ✅ CUSTOMERS (not "Not available for global schema")
- ✅ TICKETS (not "Not available for global schema")
- ✅ KNOWLEDGEBASE (not "Not available for global schema")
- ✅ SLA POLICIES

### 4. Add Data in This Order

**Step 1: Add an SLA Policy**
- Click "SLA Policies" under TICKETS
- Click "+ Add"
- Fill in:
  - Name: "High Priority SLA"
  - Priority: "High"
  - Resolution time: 60 (minutes)
  - Is active: ✓
- Click "SAVE"

**Step 2: Add a Customer**
- Click "Customers" under CUSTOMERS
- Click "+ Add"
- Fill in:
  - Email: customer@example.com
  - Name: John Doe
  - Company: Example Corp
- Click "SAVE"

**Step 3: Add a Ticket**
- Click "Tickets" under TICKETS
- Click "+ Add"
- Fill in:
  - Title: "Need help with login"
  - Description: "I can't log into my account"
  - Status: "New"
  - Priority: "High"
  - Customer: Select the customer you just created
  - SLA Policy: Select the SLA policy you created
- Click "SAVE"

**Step 4: Add Knowledge Base Article (Optional)**
- Click "Knowledge Bases" under KNOWLEDGEBASE
- Click "+ Add"
- Fill in:
  - Title: "How to reset password"
  - Content: "To reset your password..."
  - Category: "General"
  - Is published: ✓
- Click "SAVE"

## Accessing the API

Once you have data, you can access the API:

- **Tickets API**: http://acme.localhost:8000/api/tickets/
- **Customers API**: http://acme.localhost:8000/api/customers/
- **Knowledge Base API**: http://acme.localhost:8000/api/articles/
- **SLA Policies API**: http://acme.localhost:8000/api/sla-policies/

## Important Notes

- **Public Schema** (`localhost:8000/admin/`) = Only for managing tenants
- **Tenant Schema** (`acme.localhost:8000/admin/`) = For managing tickets, customers, etc.
- Always access tenant-specific data via the tenant domain (acme.localhost)
- Each tenant has completely isolated data

