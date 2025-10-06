# AnyCRM

A simple, self-contained CRM application built with Python, FastAPI, and SQLite. Perfect for learning, prototyping, or as a starting point for your own CRM system.

## Features

- **Two-table database**: Accounts and Contacts with relationship support
- **Web UI**: Clean, responsive interface for CRUD operations
- **REST API**: Full REST API with Bearer token authentication and automatic OpenAPI documentation
- **AI Agent Integration**: Account enrichment via AnyQuest AI agents with real-time WebSocket updates
- **Self-contained**: Uses SQLite - no external database required
- **Easy deployment**: Works on Replit, local machines, and cloud platforms

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation & Running

#### On Mac/Linux

1. **Clone or download this repository**
   ```bash
   git clone <your-repo-url>
   cd AnyCRM
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the application**
   - Web UI: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative API Documentation: http://localhost:8000/redoc

#### On Windows

1. **Clone or download this repository**
   ```cmd
   git clone <your-repo-url>
   cd AnyCRM
   ```

2. **Create a virtual environment** (recommended)
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```cmd
   python main.py
   ```

5. **Access the application**
   - Web UI: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative API Documentation: http://localhost:8000/redoc

### Running on Replit

1. Fork or import this repository to Replit
2. Replit will automatically detect the Python environment
3. Click the "Run" button
4. The application will start and be accessible via the Replit URL

## Project Structure

```
AnyCRM/
├── main.py              # Main application file with FastAPI routes
├── database.py          # Database models and initialization
├── config.py            # Configuration management
├── migrate_db.py        # Database migration script
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── config.json         # Configuration file (created automatically)
├── anycrm.db           # SQLite database (created automatically)
├── templates/          # HTML templates for web UI
│   ├── base.html       # Base template with common layout
│   ├── accounts.html   # Accounts list page
│   ├── account_form.html # Account create/edit form
│   ├── account_detail.html # Account detail page with enrichment
│   ├── contacts.html   # Contacts list page
│   ├── contact_form.html # Contact create/edit form
│   └── settings.html   # Settings page
└── static/             # Static files (currently empty)
```

## Database Schema

### Accounts Table
- `id` - Integer, Primary Key, Auto-increment
- `name` - Text, Required
- `industry` - Text, Optional (dropdown selection)
- `website` - Text, Optional
- `notes` - Text, Optional
- `state` - Integer, Default 0 (internal: 0=ready, 1=enriching)
- `created_at` - Timestamp, Auto-generated

### Contacts Table
- `id` - Integer, Primary Key, Auto-increment
- `account_id` - Integer, Foreign Key to Accounts, Optional
- `first_name` - Text, Required
- `last_name` - Text, Required
- `title` - Text, Optional
- `email` - Text, Optional
- `linkedin` - Text, Optional
- `notes` - Text, Optional
- `created_at` - Timestamp, Auto-generated

## REST API Endpoints

All REST API endpoints require Bearer token authentication. Include your API key in the `Authorization` header:
```
Authorization: Bearer YOUR_API_KEY
```

You can find your API key in the Settings page after starting the application.

### Accounts

- `POST /api/accounts` - Create a new account
- `GET /api/accounts` - Get all accounts
- `GET /api/accounts/{id}` - Get a specific account
- `PUT /api/accounts/{id}` - Update an account
- `DELETE /api/accounts/{id}` - Delete an account

### Contacts

- `POST /api/contacts` - Create a new contact
- `GET /api/contacts` - Get all contacts
- `GET /api/contacts/{id}` - Get a specific contact
- `PUT /api/contacts/{id}` - Update a contact
- `DELETE /api/contacts/{id}` - Delete a contact

### API Documentation

The OpenAPI specification is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs (click "Authorize" to enter your API key)
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Usage Examples

### Using the Web UI

1. Navigate to http://localhost:8000
2. Use the navigation menu to switch between Accounts, Contacts, and Settings
3. Click "New Account" or "New Contact" to create records
4. Click on an account name to view details and associated contacts
5. Click "Enrich Account" to trigger AI-powered account enrichment (requires AnyQuest API key)
6. Click "Edit" to modify existing records
7. Click "Delete" to remove records (with confirmation)

### Configuring AI Agent Integration

1. Navigate to Settings (http://localhost:8000/settings)
2. Under "AnyQuest Agent Configuration", enter your AnyQuest API key and URL
3. The Base URL is automatically configured for your application server
4. Save the configuration
5. Go to any account detail page and click "Enrich Account" to trigger enrichment
6. The page will update in real-time when enrichment completes

### Using the REST API

Replace `YOUR_API_KEY` with your actual API key from the Settings page.

#### Create an Account
```bash
curl -X POST "http://localhost:8000/api/accounts" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "industry": "Technology",
    "website": "https://acme.com",
    "notes": "Potential client"
  }'
```

#### Get All Accounts
```bash
curl "http://localhost:8000/api/accounts" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Create a Contact
```bash
curl -X POST "http://localhost:8000/api/contacts" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "title": "CEO",
    "email": "john.doe@acme.com",
    "linkedin": "https://linkedin.com/in/johndoe",
    "account_id": 1
  }'
```

#### Update a Contact
```bash
curl -X PUT "http://localhost:8000/api/contacts/1" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Manager",
    "notes": "Prefers email communication"
  }'
```

#### Delete an Account
```bash
curl -X DELETE "http://localhost:8000/api/accounts/1" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Development

### Running in Development Mode

The application runs with auto-reload enabled by default. Any changes to the Python files will automatically restart the server.

### Customization

- **Styling**: Modify `templates/base.html` to change the look and feel
- **Database**: Add fields by modifying `database.py` and `main.py`
- **Features**: Add new endpoints in `main.py`

## Technologies Used

- **FastAPI** - Modern, fast web framework for building APIs
- **Uvicorn** - ASGI server for running FastAPI applications
- **SQLite** - Lightweight, serverless database
- **Jinja2** - Template engine for rendering HTML
- **WebSockets** - Real-time communication for enrichment updates
- **httpx** - Async HTTP client for API calls
- **Python 3.8+** - Programming language

## License

This project is open source and available for educational and commercial use.

## Contributing

Feel free to fork this project and customize it for your needs. Pull requests are welcome!

## Troubleshooting

### Port Already in Use
If port 8000 is already in use, modify the `main.py` file and change the port number:
```python
uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
```

### Database Issues
If you encounter database errors about missing columns, run the migration script:
```bash
python migrate_db.py
```

To start completely fresh, delete `anycrm.db` and restart the application to create a new database.

### Module Not Found Errors
Make sure you've activated your virtual environment and installed all dependencies:
```bash
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```
