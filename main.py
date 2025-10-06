"""Main application file for AnyCRM - A simple CRM with REST API and Web UI."""
from fastapi import FastAPI, HTTPException, Request, Form, WebSocket, WebSocketDisconnect, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
import httpx
import json
from uuid import uuid4
from database import init_database, get_db, dict_from_row
from config import get_config, update_config


# Initialize FastAPI app with security
app = FastAPI(
    title="AnyCRM API",
    description="A simple CRM system with REST API for managing accounts and contacts",
    version="1.0.0",
    openapi_tags=[
        {"name": "accounts", "description": "Operations with accounts"},
        {"name": "contacts", "description": "Operations with contacts"}
    ]
)

# Security scheme
security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Bearer token."""
    config = get_config()
    if credentials.credentials != config.get("api_key"):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# Setup templates
templates = Jinja2Templates(directory="templates")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, account_id: str):
        await websocket.accept()
        if account_id not in self.active_connections:
            self.active_connections[account_id] = []
        self.active_connections[account_id].append(websocket)

    def disconnect(self, websocket: WebSocket, account_id: str):
        if account_id in self.active_connections:
            self.active_connections[account_id].remove(websocket)
            if not self.active_connections[account_id]:
                del self.active_connections[account_id]

    async def send_message(self, account_id: str, message: dict):
        if account_id in self.active_connections:
            for connection in self.active_connections[account_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()


# Industry options
INDUSTRIES = [
    "Technology",
    "Healthcare",
    "Finance",
    "Manufacturing",
    "Retail",
    "Education",
    "Real Estate",
    "Consulting",
    "Media & Entertainment",
    "Transportation",
    "Hospitality",
    "Energy",
    "Telecommunications",
    "Construction",
    "Agriculture",
    "Other"
]

# Pydantic models for API
class AccountCreate(BaseModel):
    name: str = Field(..., description="Company or account name")
    industry: Optional[str] = Field(None, description="Industry sector (e.g., Technology, Healthcare, Finance)")
    website: Optional[str] = Field(None, description="Company website URL")
    notes: Optional[str] = Field(None, description="Additional notes or information about the account")


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Company or account name")
    industry: Optional[str] = Field(None, description="Industry sector (e.g., Technology, Healthcare, Finance)")
    website: Optional[str] = Field(None, description="Company website URL")
    notes: Optional[str] = Field(None, description="Additional notes or information about the account")


class ContactCreate(BaseModel):
    account_id: Optional[int] = Field(None, description="ID of the associated account")
    first_name: str = Field(..., description="Contact's first name")
    last_name: str = Field(..., description="Contact's last name")
    title: Optional[str] = Field(None, description="Job title or position")
    email: Optional[str] = Field(None, description="Email address")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    notes: Optional[str] = Field(None, description="Additional notes about the contact")


class ContactUpdate(BaseModel):
    account_id: Optional[int] = Field(None, description="ID of the associated account")
    first_name: Optional[str] = Field(None, description="Contact's first name")
    last_name: Optional[str] = Field(None, description="Contact's last name")
    title: Optional[str] = Field(None, description="Job title or position")
    email: Optional[str] = Field(None, description="Email address")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    notes: Optional[str] = Field(None, description="Additional notes about the contact")


# ============================================================================
# REST API ENDPOINTS - ACCOUNTS
# ============================================================================

@app.post("/api/accounts", status_code=201, tags=["accounts"])
async def create_account(account: AccountCreate, api_key: str = Depends(verify_api_key)):
    """Create a new account."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO accounts (name, industry, website, notes)
               VALUES (?, ?, ?, ?)""",
            (account.name, account.industry, account.website, account.notes)
        )
        conn.commit()
        account_id = cursor.lastrowid

        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        return dict_from_row(cursor.fetchone())


@app.get("/api/accounts", tags=["accounts"])
async def get_accounts(api_key: str = Depends(verify_api_key)):
    """Get all accounts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY created_at DESC")
        accounts = [dict_from_row(row) for row in cursor.fetchall()]
        return accounts


@app.get("/api/accounts/{account_id}", tags=["accounts"])
async def get_account(account_id: int, api_key: str = Depends(verify_api_key)):
    """Get a specific account by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        account = dict_from_row(cursor.fetchone())

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        return account


@app.put("/api/accounts/{account_id}", tags=["accounts"])
async def update_account(account_id: int, account: AccountUpdate, api_key: str = Depends(verify_api_key)):
    """Update an existing account."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if account exists
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Account not found")

        # Build update query dynamically
        updates = []
        values = []
        for field, value in account.dict(exclude_unset=True).items():
            updates.append(f"{field} = ?")
            values.append(value)

        if updates:
            values.append(account_id)
            query = f"UPDATE accounts SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        return dict_from_row(cursor.fetchone())


@app.delete("/api/accounts/{account_id}", status_code=204, tags=["accounts"])
async def delete_account(account_id: int, api_key: str = Depends(verify_api_key)):
    """Delete an account."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Account not found")

        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()
        return None


# ============================================================================
# REST API ENDPOINTS - CONTACTS
# ============================================================================

@app.post("/api/contacts", status_code=201, tags=["contacts"])
async def create_contact(contact: ContactCreate, api_key: str = Depends(verify_api_key)):
    """Create a new contact."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO contacts (account_id, first_name, last_name, title, email, linkedin, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (contact.account_id, contact.first_name, contact.last_name,
             contact.title, contact.email, contact.linkedin, contact.notes)
        )
        conn.commit()
        contact_id = cursor.lastrowid

        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        return dict_from_row(cursor.fetchone())


@app.get("/api/contacts", tags=["contacts"])
async def get_contacts(api_key: str = Depends(verify_api_key)):
    """Get all contacts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
        contacts = [dict_from_row(row) for row in cursor.fetchall()]
        return contacts


@app.get("/api/contacts/{contact_id}", tags=["contacts"])
async def get_contact(contact_id: int, api_key: str = Depends(verify_api_key)):
    """Get a specific contact by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        contact = dict_from_row(cursor.fetchone())

        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        return contact


@app.put("/api/contacts/{contact_id}", tags=["contacts"])
async def update_contact(contact_id: int, contact: ContactUpdate, api_key: str = Depends(verify_api_key)):
    """Update an existing contact."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if contact exists
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")

        # Build update query dynamically
        updates = []
        values = []
        for field, value in contact.dict(exclude_unset=True).items():
            updates.append(f"{field} = ?")
            values.append(value)

        if updates:
            values.append(contact_id)
            query = f"UPDATE contacts SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        return dict_from_row(cursor.fetchone())


@app.delete("/api/contacts/{contact_id}", status_code=204, tags=["contacts"])
async def delete_contact(contact_id: int, api_key: str = Depends(verify_api_key)):
    """Delete a contact."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        return None


# ============================================================================
# WEB UI ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    """Home page - redirect to accounts."""
    return RedirectResponse(url="/accounts")


@app.get("/accounts", response_class=HTMLResponse, include_in_schema=False)
async def accounts_page(request: Request):
    """Display all accounts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY created_at DESC")
        accounts = [dict_from_row(row) for row in cursor.fetchall()]

    return templates.TemplateResponse("accounts.html", {
        "request": request,
        "accounts": accounts
    })


@app.get("/accounts/{account_id}", response_class=HTMLResponse, include_in_schema=False)
async def account_detail_page(request: Request, account_id: int):
    """Display account details and associated contacts."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get account details
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        account = dict_from_row(cursor.fetchone())

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Get contacts for this account
        cursor.execute(
            "SELECT * FROM contacts WHERE account_id = ? ORDER BY last_name, first_name",
            (account_id,)
        )
        contacts = [dict_from_row(row) for row in cursor.fetchall()]

    return templates.TemplateResponse("account_detail.html", {
        "request": request,
        "account": account,
        "contacts": contacts
    })


@app.get("/accounts/new", response_class=HTMLResponse, include_in_schema=False)
async def new_account_page(request: Request):
    """Display form to create new account."""
    return templates.TemplateResponse("account_form.html", {
        "request": request,
        "account": None,
        "industries": INDUSTRIES,
        "action": "/accounts/create"
    })


@app.post("/accounts/create", include_in_schema=False)
async def create_account_form(
    name: str = Form(...),
    industry: str = Form(""),
    website: str = Form(""),
    notes: str = Form("")
):
    """Handle account creation from form."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO accounts (name, industry, website, notes)
               VALUES (?, ?, ?, ?)""",
            (name, industry or None, website or None, notes or None)
        )
        conn.commit()

    return RedirectResponse(url="/accounts", status_code=303)


@app.get("/accounts/{account_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_account_page(request: Request, account_id: int):
    """Display form to edit account."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        account = dict_from_row(cursor.fetchone())

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return templates.TemplateResponse("account_form.html", {
        "request": request,
        "account": account,
        "industries": INDUSTRIES,
        "action": f"/accounts/{account_id}/update"
    })


@app.post("/accounts/{account_id}/update", include_in_schema=False)
async def update_account_form(
    account_id: int,
    name: str = Form(...),
    industry: str = Form(""),
    website: str = Form(""),
    notes: str = Form("")
):
    """Handle account update from form."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE accounts
               SET name = ?, industry = ?, website = ?, notes = ?
               WHERE id = ?""",
            (name, industry or None, website or None, notes or None, account_id)
        )
        conn.commit()

    return RedirectResponse(url="/accounts", status_code=303)


@app.post("/accounts/{account_id}/delete", include_in_schema=False)
async def delete_account_form(account_id: int):
    """Handle account deletion from form."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()

    return RedirectResponse(url="/accounts", status_code=303)


@app.get("/contacts", response_class=HTMLResponse, include_in_schema=False)
async def contacts_page(request: Request):
    """Display all contacts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, a.name as account_name
            FROM contacts c
            LEFT JOIN accounts a ON c.account_id = a.id
            ORDER BY c.created_at DESC
        """)
        contacts = [dict_from_row(row) for row in cursor.fetchall()]

    return templates.TemplateResponse("contacts.html", {
        "request": request,
        "contacts": contacts
    })


@app.get("/contacts/new", response_class=HTMLResponse, include_in_schema=False)
async def new_contact_page(request: Request):
    """Display form to create new contact."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY name")
        accounts = [dict_from_row(row) for row in cursor.fetchall()]

    return templates.TemplateResponse("contact_form.html", {
        "request": request,
        "contact": None,
        "accounts": accounts,
        "action": "/contacts/create"
    })


@app.post("/contacts/create", include_in_schema=False)
async def create_contact_form(
    first_name: str = Form(...),
    last_name: str = Form(...),
    account_id: Optional[int] = Form(None),
    title: str = Form(""),
    email: str = Form(""),
    linkedin: str = Form(""),
    notes: str = Form("")
):
    """Handle contact creation from form."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO contacts (account_id, first_name, last_name, title, email, linkedin, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (account_id or None, first_name, last_name, title or None,
             email or None, linkedin or None, notes or None)
        )
        conn.commit()

    return RedirectResponse(url="/contacts", status_code=303)


@app.get("/contacts/{contact_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_contact_page(request: Request, contact_id: int):
    """Display form to edit contact."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        contact = dict_from_row(cursor.fetchone())

        cursor.execute("SELECT * FROM accounts ORDER BY name")
        accounts = [dict_from_row(row) for row in cursor.fetchall()]

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return templates.TemplateResponse("contact_form.html", {
        "request": request,
        "contact": contact,
        "accounts": accounts,
        "action": f"/contacts/{contact_id}/update"
    })


@app.post("/contacts/{contact_id}/update", include_in_schema=False)
async def update_contact_form(
    contact_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    account_id: Optional[int] = Form(None),
    title: str = Form(""),
    email: str = Form(""),
    linkedin: str = Form(""),
    notes: str = Form("")
):
    """Handle contact update from form."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE contacts
               SET account_id = ?, first_name = ?, last_name = ?, title = ?, email = ?, linkedin = ?, notes = ?
               WHERE id = ?""",
            (account_id or None, first_name, last_name, title or None,
             email or None, linkedin or None, notes or None, contact_id)
        )
        conn.commit()

    return RedirectResponse(url="/contacts", status_code=303)


@app.post("/contacts/{contact_id}/delete", include_in_schema=False)
async def delete_contact_form(contact_id: int):
    """Handle contact deletion from form."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()

    return RedirectResponse(url="/contacts", status_code=303)


# ============================================================================
# SETTINGS PAGE
# ============================================================================

@app.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request):
    """Display settings page."""
    config = get_config()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": config
    })


@app.post("/settings/save", include_in_schema=False)
async def save_settings(
    api_key: str = Form(""),
    base_url: str = Form("http://localhost:8000"),
    anyquest_api_key: str = Form(""),
    anyquest_api_url: str = Form("https://api.anyquest.ai")
):
    """Save settings."""
    update_config({
        "api_key": api_key,
        "base_url": base_url,
        "anyquest_api_key": anyquest_api_key,
        "anyquest_api_url": anyquest_api_url
    })
    return RedirectResponse(url="/settings", status_code=303)


# ============================================================================
# AGENT ENRICHMENT ENDPOINTS
# ============================================================================

@app.post("/accounts/{account_id}/enrich", include_in_schema=False)
async def enrich_account(account_id: int, instructions: str = Form("")):
    """Trigger account enrichment via AnyQuest agent."""
    config = get_config()

    if not config.get("anyquest_api_key"):
        raise HTTPException(status_code=400, detail="AnyQuest API key not configured. Please configure in Settings.")

    # Get account details and set state to 1 (enriching)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        account = dict_from_row(cursor.fetchone())

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Set state to 1 (enriching)
        cursor.execute("UPDATE accounts SET state = 1 WHERE id = ?", (account_id,))
        conn.commit()

    # Create prompt JSON
    prompt_data = {
        "account": {
            "id": account["id"],
            "name": account["name"],
            "industry": account.get("industry"),
            "website": account.get("website"),
            "notes": account.get("notes")
        },
    }

    # Only include instructions if provided
    if instructions and instructions.strip():
        prompt_data["instructions"] = instructions

    prompt_text = json.dumps(prompt_data, indent=2)

    # Call AnyQuest API
    webhook_url = f"{config.get('base_url')}/webhook/{account_id}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{config['anyquest_api_url']}/run",
                json={
                    "prompt": prompt_text,
                    "webhook": webhook_url
                },
                headers={
                    "x-api-key": config["anyquest_api_key"],
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling AnyQuest API: {str(e)}")

    return {"status": "success", "message": "Enrichment started"}


# ============================================================================
# WEBHOOK AND WEBSOCKET ENDPOINTS
# ============================================================================

@app.post("/webhook/{account_id}", include_in_schema=False)
async def webhook_handler(account_id: int, request: Request):
    """Handle webhook callback from AnyQuest agent."""
    event_type = request.headers.get("aq-event-type", "response")
    body = await request.body()

    if event_type == "response":
        # Reset account state to 0 (ready)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET state = 0 WHERE id = ?", (account_id,))
            conn.commit()

        # Agent completed - notify connected clients
        await manager.send_message(str(account_id), {
            "type": "enrichment_complete",
            "account_id": account_id,
            "message": body.decode('utf-8') if body else "Enrichment completed"
        })

    return {"status": "received"}


@app.websocket("/ws/account/{account_id}")
async def websocket_endpoint(websocket: WebSocket, account_id: int):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, str(account_id))
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, str(account_id))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
