from typing import Optional, Dict, Literal
from mcp.server.fastmcp import FastMCP

from app.salesforce_client import SalesforceClient
from app.audit_logger import audit_log
from app.utils import generate_correlation_id
from app.config import SF_INSTANCE_URL

mcp = FastMCP("Salesforce MCP")
sf = SalesforceClient()


def response(success: bool, data=None, error=None, cid=None):
    return {
        "success": success,
        "data": data,
        "error": error,
        "correlation_id": cid,
    }


# ---------------- LIST ----------------
@mcp.tool()
def list_leads(
    status: Optional[str] = None,
    email: Optional[str] = None,
    limit: int = 50,
    cursor: Optional[str] = None,
) -> Dict:
    cid = generate_correlation_id()

    if cursor:
        result = sf._request("GET", f"{SF_INSTANCE_URL}{cursor}")
    else:
        soql = "SELECT Id, Email, FirstName, LastName, Status, IsConverted FROM Lead"
        filters = []

        if status:
            filters.append(f"Status='{status}'")
        if email:
            filters.append(f"Email='{email}'")

        if filters:
            soql += " WHERE " + " AND ".join(filters)

        soql += f" LIMIT {min(limit, 100)}"
        result = sf.query(soql)

    data = {
        "records": result.get("records", []),
        "count": len(result.get("records", [])),
        "next_cursor": result.get("nextRecordsUrl"),
        "done": result.get("done", True),
    }

    audit_log("list_leads", {"status": status, "email": email}, "ok", "success", cid)
    return response(True, data, cid=cid)


# ---------------- GET ----------------
@mcp.tool()
def salesforce_get_lead(email: str) -> Dict:
    cid = generate_correlation_id()

    if not email:
        return response(False, error="Email required", cid=cid)

    result = sf.query(
        f"""
        SELECT Id, Email, Status, IsConverted
        FROM Lead
        WHERE Email='{email}'
        LIMIT 1
        """
    )

    lead = result["records"][0] if result["records"] else None
    audit_log("salesforce_get_lead", {"email": email}, {"found": bool(lead)}, "success", cid)

    return response(True, {"lead": lead}, cid=cid)


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

    if not email:
        return response(False, error="Email required", cid=cid)

    existing = salesforce_get_lead(email)["data"]["lead"]
    if existing:
        if existing["IsConverted"]:
            return response(
                True,
                {
                    "lead_id": existing["Id"],
                    "skipped": True,
                    "reason": "lead_already_converted",
                },
                cid=cid,
            )

        sf.update_lead(existing["Id"], {"LastName": last_name, "Company": company})
        audit_log("salesforce_create_lead", {"email": email}, "duplicate", "success", cid)
        return response(True, {"lead_id": existing["Id"], "duplicate": True}, cid)

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
    return response(True, result, cid)


# ---------------- UPDATE ----------------
@mcp.tool()
def salesforce_update_lead(
    lead_id: Optional[str] = None,
    email: Optional[str] = None,
    fields: Optional[Dict[str, str]] = None,
) -> Dict:
    cid = generate_correlation_id()

    if not fields:
        return response(False, error="No fields to update", cid=cid)

    if not lead_id:
        if not email:
            return response(False, error="lead_id or email required", cid=cid)

        lead = salesforce_get_lead(email)["data"]["lead"]
        if not lead:
            return response(False, error="Lead not found", cid=cid)

        if lead["IsConverted"]:
            return response(
                True,
                {
                    "lead_id": lead["Id"],
                    "skipped": True,
                    "reason": "lead_already_converted",
                },
                cid=cid,
            )

        lead_id = lead["Id"]

    sf.update_lead(lead_id, fields)
    audit_log("salesforce_update_lead", fields, "updated", "success", cid)
    return response(True, {"lead_id": lead_id, "updated": True}, cid)


# ---------------- DELETE ----------------
@mcp.tool()
def salesforce_delete_lead(lead_id: str) -> Dict:
    cid = generate_correlation_id()

    if not lead_id:
        return response(False, error="lead_id required", cid=cid)

    sf.delete_lead(lead_id)
    audit_log("salesforce_delete_lead", {"lead_id": lead_id}, "deleted", "success", cid)
    return response(True, {"deleted": True}, cid)


# ---------------- STATUS ----------------
@mcp.tool()
def salesforce_update_lead_status(
    status: Literal["scheduled", "objected"],
    lead_id: Optional[str] = None,
    email: Optional[str] = None,
) -> Dict:
    cid = generate_correlation_id()

    if not lead_id and not email:
        return response(False, error="lead_id or email required", cid=cid)

    if not lead_id:
        lead = salesforce_get_lead(email)["data"]["lead"]
        if not lead:
            return response(False, error="Lead not found", cid=cid)

        if lead["IsConverted"]:
            return response(
                True,
                {
                    "lead_id": lead["Id"],
                    "skipped": True,
                    "reason": "lead_already_converted",
                },
                cid=cid,
            )

        lead_id = lead["Id"]

    if status == "scheduled":
        result = sf.convert_lead(lead_id)
    else:
        sf.update_lead(lead_id, {"Status": "Not Converted"})
        result = {"lead_id": lead_id, "status": "Not Converted"}

    audit_log("salesforce_update_lead_status", {"lead_id": lead_id}, result, "success", cid)
    return response(True, result, cid)


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

    if not email:
        return response(False, error="Email required", cid=cid)

    lead = salesforce_get_lead(email)["data"]["lead"]

    payload = {"LastName": last_name, "Company": company}
    if first_name:
        payload["FirstName"] = first_name
    if phone:
        payload["Phone"] = phone
    if source:
        payload["LeadSource"] = source

    if lead:
        if lead["IsConverted"]:
            audit_log(
                "salesforce_sync_lead",
                {"email": email, "lead_id": lead["Id"]},
                "skipped_converted_lead",
                "success",
                cid,
            )
            return response(
                True,
                {
                    "lead_id": lead["Id"],
                    "skipped": True,
                    "reason": "lead_already_converted",
                },
                cid=cid,
            )

        sf.update_lead(lead["Id"], payload)
        lead_id = lead["Id"]

    else:
        payload["Email"] = email
        payload["Status"] = "Contacted"
        lead_id = sf.create_lead(payload)["id"]

    if platform_status == "scheduled":
        sf.convert_lead(lead_id)
    elif platform_status == "objected":
        sf.update_lead(lead_id, {"Status": "Not Converted"})

    audit_log("salesforce_sync_lead", {"email": email}, "synced", "success", cid)
    return response(True, {"lead_id": lead_id, "synced": True}, cid)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
