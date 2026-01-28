from typing import Optional, Dict, Literal
from mcp.server.fastmcp import FastMCP

from app.salesforce_client import SalesforceClient
from app.audit_logger import audit_log
from app.utils import generate_correlation_id

mcp = FastMCP("Salesforce MCP")
sf = SalesforceClient()


# ---------------- LIST ----------------
@mcp.tool()
def list_leads(
    status: Optional[str] = None,
    email: Optional[str] = None,
    limit: int = 50,
) -> Dict:
    cid = generate_correlation_id()

    try:
        soql = "SELECT Id, Email, FirstName, LastName, Status FROM Lead"
        filters = []

        if status:
            filters.append(f"Status='{status}'")
        if email:
            filters.append(f"Email='{email}'")

        if filters:
            soql += " WHERE " + " AND ".join(filters)

        soql += f" LIMIT {min(limit,100)}"

        result = sf.query(soql)

        audit_log("list_leads", {"status": status, "email": email}, "success", "success", cid)
        return {"records": result.get("records", [])}

    except Exception as e:
        audit_log("list_leads", {}, str(e), "error", cid)
        raise


# ---------------- GET ----------------
@mcp.tool()
def salesforce_get_lead(email: str) -> Dict:
    cid = generate_correlation_id()

    result = sf.query(
        f"SELECT Id, Email, Status FROM Lead WHERE Email='{email}' LIMIT 1"
    )

    lead = result["records"][0] if result["records"] else None
    audit_log("salesforce_get_lead", {"email": email}, {"found": bool(lead)}, "success", cid)

    return {"lead": lead}


# ---------------- CREATE ----------------
@mcp.tool()
def salesforce_create_lead(
    email: str,
    last_name: str,
    first_name: Optional[str] = None,
    phone: Optional[str] = None,
    company: str = "Individual",
    source: Optional[str] = None,
) -> Dict:
    cid = generate_correlation_id()

    payload = {
        "Email": email,
        "LastName": last_name,
        "Company": company,
        "Status": "Contacted",
    }

    if first_name:
        payload["FirstName"] = first_name
    if phone:
        payload["Phone"] = phone
    if source:
        payload["LeadSource"] = source

    result = sf.create_lead(payload)
    audit_log("salesforce_create_lead", {"email": email}, result, "success", cid)

    return result


# ---------------- UPDATE ----------------
@mcp.tool()
def salesforce_update_lead(
    lead_id: Optional[str] = None,
    email: Optional[str] = None,
    fields: Dict[str, str] = {},
) -> Dict:
    cid = generate_correlation_id()

    if not lead_id:
        lookup = salesforce_get_lead(email)
        if not lookup["lead"]:
            return {"error": "Lead not found"}
        lead_id = lookup["lead"]["Id"]

    sf.update_lead(lead_id, fields)
    audit_log("salesforce_update_lead", fields, "updated", "success", cid)

    return {"updated": True, "lead_id": lead_id}


# ---------------- DELETE ----------------
@mcp.tool()
def salesforce_delete_lead(lead_id: str) -> Dict:
    cid = generate_correlation_id()
    sf.delete_lead(lead_id)
    audit_log("salesforce_delete_lead", {"lead_id": lead_id}, "deleted", "success", cid)
    return {"deleted": True}


# ---------------- STATUS ----------------
@mcp.tool()
def salesforce_update_lead_status(
    status: Literal["scheduled", "objected"],
    lead_id: Optional[str] = None,
    email: Optional[str] = None,
) -> Dict:
    cid = generate_correlation_id()

    if not lead_id:
        lookup = salesforce_get_lead(email)
        lead = lookup["lead"]
        if not lead:
            return {"error": "Lead not found"}

        if lead["Status"] == "Not Converted":
            audit_log("salesforce_update_lead_status", {}, "blocked", "blocked", cid)
            return {"blocked": True}

        lead_id = lead["Id"]

    if status == "scheduled":
        sf.convert_lead(lead_id)
        result = {"status": "Converted"}
    else:
        sf.update_lead(lead_id, {"Status": "Not Converted"})
        result = {"status": "Not Converted"}

    audit_log("salesforce_update_lead_status", {"status": status}, result, "success", cid)
    return result


# ---------------- SYNC ----------------
@mcp.tool()
def salesforce_sync_lead(
    email: str,
    last_name: str,
    first_name: Optional[str] = None,
    phone: Optional[str] = None,
    company: str = "Individual",
    source: Optional[str] = None,
    platform_status: Optional[Literal["scheduled", "objected"]] = None,
) -> Dict:
    cid = generate_correlation_id()

    lookup = salesforce_get_lead(email)
    lead = lookup["lead"]

    payload = {"LastName": last_name, "Company": company}

    if first_name:
        payload["FirstName"] = first_name
    if phone:
        payload["Phone"] = phone
    if source:
        payload["LeadSource"] = source

    if lead:
        if lead["Status"] == "Not Converted":
            audit_log("salesforce_sync_lead", {"email": email}, "blocked", "blocked", cid)
            return {"blocked": True}

        sf.update_lead(lead["Id"], payload)
        lead_id = lead["Id"]
    else:
        payload["Email"] = email
        payload["Status"] = "Contacted"
        lead_id = sf.create_lead(payload)["id"]

    if platform_status:
        salesforce_update_lead_status(platform_status, lead_id=lead_id)

    audit_log("salesforce_sync_lead", {"email": email}, "synced", "success", cid)
    return {"lead_id": lead_id, "synced": True}


# ---------------- RUN ----------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
