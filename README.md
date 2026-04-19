# Spendwise — Expense Tracker

A clean, full-stack expense tracker built with **Flask + SQLite**, ready to deploy to **Azure App Service**.

---

## Project Structure

```
expense-tracker/
├── app.py                  ← Flask backend (routes, SQLite logic)
├── azure_integration.py    ← Optional: swap SQLite → Azure Table Storage
├── requirements.txt
├── startup.txt             ← Azure startup command
├── templates/
│   └── index.html          ← Jinja2 HTML template
└── static/
    └── style.css           ← All styling
```

---

## Run Locally

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python app.py
# → Open http://localhost:5000
```

---

## Deploy to Azure App Service

### Prerequisites
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- An Azure account (`az login`)

### Step-by-step

```bash
# 1. Login
az login

# 2. Create a resource group
az group create --name expense-tracker-rg --location eastus

# 3. Create an App Service plan (Free tier)
az appservice plan create \
  --name expense-tracker-plan \
  --resource-group expense-tracker-rg \
  --sku FREE \
  --is-linux

# 4. Create the web app (Python 3.11)
az webapp create \
  --name spendwise-app \
  --resource-group expense-tracker-rg \
  --plan expense-tracker-plan \
  --runtime "PYTHON:3.11"

# 5. Set startup command (gunicorn)
az webapp config set \
  --name spendwise-app \
  --resource-group expense-tracker-rg \
  --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app"

# 6. Deploy via ZIP
zip -r app.zip . -x "venv/*" "*.pyc" "__pycache__/*"
az webapp deployment source config-zip \
  --name spendwise-app \
  --resource-group expense-tracker-rg \
  --src app.zip

# 7. Open in browser
az webapp browse --name spendwise-app --resource-group expense-tracker-rg
```

---

## Azure Table Storage (optional)

To persist data in Azure instead of SQLite:

```bash
# Create a storage account
az storage account create \
  --name spendwisestorage \
  --resource-group expense-tracker-rg \
  --location eastus \
  --sku Standard_LRS

# Get the connection string
az storage account show-connection-string \
  --name spendwisestorage \
  --resource-group expense-tracker-rg

# Set it as an app setting
az webapp config appsettings set \
  --name spendwise-app \
  --resource-group expense-tracker-rg \
  --settings AZURE_STORAGE_CONNECTION_STRING="<your-connection-string>"
```

Then use the helpers in `azure_integration.py` instead of SQLite in `app.py`.

---

## Azure SQL Database (alternative)

```bash
# Create a flexible server
az sql server create \
  --name spendwise-sql \
  --resource-group expense-tracker-rg \
  --location eastus \
  --admin-user sqladmin \
  --admin-password "YourP@ssword123"

# Create a database
az sql db create \
  --server spendwise-sql \
  --resource-group expense-tracker-rg \
  --name expensesdb \
  --service-objective Basic
```

Replace SQLite queries in `app.py` with `pyodbc` connections using the Azure SQL connection string.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Table Storage |
| `SQLAZURECONNSTR_EXPENSES` | Azure SQL Database |
| `SECRET_KEY` | Flask session secret |
