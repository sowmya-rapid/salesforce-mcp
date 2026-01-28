# Salesforce MCP Server

A TRD-compliant Salesforce CRM integration implemented as an MCP (Model Context Protocol) server.  
It exposes Salesforce Lead operations as safe, deterministic tools for AI agents and workflows.

## Features
- OAuth 2.0 (refresh-token flow)
- Lead CRUD operations
- Lead conversion via SOAP
- Idempotent lead sync
- Safe handling of disqualified leads
- Full audit logging (TRD requirement)
- Windows + PowerShell friendly



## Environment Variables
Create a `.env` file:

SF_CLIENT_ID=your_client_id   
SF_CLIENT_SECRET=your_client_secret   
SF_REFRESH_TOKEN=your_refresh_token   
SF_INSTANCE_URL=https://your-org.my.salesforce.com   
SF_TOKEN_URL=https://login.salesforce.com/services/oauth2/token   
SF_API_VERSION=v59.0


## Run (PowerShell)
uv run python -m app.server


## MCP Tools
- list_leads  
- salesforce_get_lead  
- salesforce_create_lead  
- salesforce_update_lead  
- salesforce_delete_lead  
- salesforce_update_lead_status  
- salesforce_sync_lead  

## Audit Logging
All tool calls are logged with:
- tool name
- inputs (sanitized)
- result & status
- timestamp
- correlation ID

Logs are written to:
logs/audit.log


## TRD Compliance
- OAuth refresh token flow
- Deterministic MCP tools
- Idempotent operations
- Safe lead conversion
- Full audit logging


