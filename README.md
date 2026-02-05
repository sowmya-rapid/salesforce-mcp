# Salesforce MCP Server

A **Model Context Protocol (MCP)** server for **Salesforce CRM integration**. This server provides tools to interact with Salesforce Leads through the MCP protocol, enabling AI assistants, workflows, and copilots to manage Salesforce CRM lead data safely.

---

## Features

### Lead Sync Integration 
- **Automated Lead Syncing**: Sync leads from your platform into Salesforce CRM using a safe upsert-like flow
- **Duplicate Prevention**: Checks existing leads by email before creating a new one
- **Idempotent Operations**: Safe to call multiple times with the same data - no duplicates
- **Lead Status Handling**:
  - `scheduled` → triggers Lead Conversion
  - `objected` → updates Lead status only (no conversion)
- **SOQL Safe Queries**: Email values are escaped to prevent query-breaking characters
- **Error Handling**: Clear validation and authentication errors returned in JSON format
- **Correlation IDs**: Every tool response contains a correlation ID for debugging

---

### Lead Management
- **Full CRUD Operations**: Complete lead management capabilities
  - List leads with limit support
  - Get lead by email
  - Create new lead
  - Update existing lead fields
  - Delete lead
  - Update lead status
  - Sync lead (upsert by email)

---

### Technical Features
- **OAuth Integration**: Accepts Salesforce bearer tokens via request headers
- **Type-Safe**: Built with Pydantic schemas for strong validation
- **Switch/Match Tool Routing**: Clean tool routing using `match case`
- **CORS Support**: Fully configurable CORS support via `config.py`
- **Streamable HTTP Transport**: Uses MCP `StreamableHTTPSessionManager`
- **Postman Compatible**: Designed to work correctly with Postman MCP testing

---

## Prerequisites

- Python 3.10 or higher
- UV package manager
- Salesforce OAuth access token + refresh token (from OAuth service)
- Salesforce instance URL

---

## Installation

1. Clone the repository:
  ```bash
    git clone <your-repo-url>
    cd salesforce-mcp
 ```
2. Install dependencies using UV:
 ```bash
    uv sync add
 ```

# Edit .env and add your Salesforce config
.env

 ```bash
    SF_CLIENT_ID=your_salesforce_client_id
    SF_CLIENT_SECRET=your_salesforce_client_secret
    
    SF_TOKEN_URL=https://login.salesforce.com/services/oauth2/token
    SF_INSTANCE_URL=https://yourInstance.my.salesforce.com
    SF_API_VERSION=v59.0
    
    MCP_HOST=0.0.0.0
    MCP_PORT=3333
 ```

# Authentication (Required Headers)
This MCP server expects authentication tokens via headers.

Required Headers Format
```bash
Authorization: Bearer <ACCESS_TOKEN>
X-SF-Refresh-Token: Bearer <REFRESH_TOKEN>
X-SF-Instance-Url: https://yourInstance.my.salesforce.com
Content-Type: application/json
Accept: application/json
```

⚠️ Important

```bash
Must include a space: Bearer <token>

Authorization:Bearer <token> ❌ will fail

Authorization: Bearer <token> ✅ correct
```
Usage
Running the Server
```bash
uv run python -m app.server
```

Server will start on:
```bash
(http://0.0.0.0:3333)
```



## Available Tools

### 1. `salesforce_sync_lead`

### 2. `salesforce_list_leads`

### 3. `salesforce_get_lead`

### 4. `salesforce_create_lead`

### 5. `salesforce_update_lead`

### 6. `salesforce_delete_lead`

### 7. `salesforce_update_lead_status`

# Response Format
All tool responses return:

```bash
{
  "success": true,
  "data": {},
  "correlation_id": "uuid",
  "status_code": 200
}
```

Validation Error Response
If validation fails, the server returns:

```bash
{
  "success": false,
  "error": "Validation Error",
  "details": [
    {
      "field": "email",
      "message": "field required"
    }
  ],
  "correlation_id": "uuid"
}
```
# Authentication Error Response
If required auth headers are missing, the server returns:

```bash
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required to access this resource",
    "details": {
      "authentication_requirements": [
        {
          "provider": "salesforce",
          "auth_type": "bearer",
          "header_name": "Authorization",
          "header_format": "Bearer {access_token}",
          "required_scopes": ["api", "refresh_token", "offline_access"],
          "token_source": "access_token"
        }
      ]
    }
  }
}
```


# Project Structure
```bash
salesforce-mcp/
├── app/
│   ├── server.py            # MCP server and tools
│   ├── salesforce_client.py # Salesforce REST/SOAP client
│   ├── schemas.py           # Pydantic request schemas
│   ├── constants.py         # Lead status + Salesforce fields/constants
│   ├── config.py            # Host/Port + CORS configuration
│   ├── utils.py             # Correlation ID + token extraction + SOQL escaping
├── tests/                   # (Optional) unit tests
├── pyproject.toml
├── .env.example
├── README.md
└── .gitignore
```

## 🐳 Docker Support
   This project is fully containerized, allowing you to run the Salesforce MCP server without installing local dependencies.

1. Build the Image
From the root directory, run:

```bash
docker build -t salesforce-mcp .
```

2. Run the Container
Ensure your .env file is populated with your Salesforce credentials, then run:

```bash
docker run -d -p 3333:3333 --name sf-server --env-file .env salesforce-mcp
```

3. Verify the Deployment
   


```bash
docker logs sf-server
```
Check if the server is active by viewing the logs    
INFO: Salesforce MCP Server active at 0.0.0.0:3333.


# License
MIT License

# Author
Sowmya ( sowmya@rapidinnovation.dev)

