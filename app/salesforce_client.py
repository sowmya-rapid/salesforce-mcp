import time
import requests
import xml.etree.ElementTree as ET

from app.config import (
    SF_CLIENT_ID,
    SF_CLIENT_SECRET,
    SF_REFRESH_TOKEN,
    SF_INSTANCE_URL,
    SF_TOKEN_URL,
    SF_API_VERSION,
)
from app.security import decrypt_token


class SalesforceClient:
    def __init__(self):
        self.access_token = None
        self.issued_at = 0
        self.refresh_token = decrypt_token(SF_REFRESH_TOKEN)

    # ---------------- AUTH ----------------
    def _refresh_token(self):
        resp = requests.post(
            SF_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": SF_CLIENT_ID,
                "client_secret": SF_CLIENT_SECRET,
                "refresh_token": self.refresh_token,
            },
        )

        if resp.status_code != 200:
            raise RuntimeError("Failed to refresh Salesforce token")

        data = resp.json()
        self.access_token = data["access_token"]
        self.issued_at = time.time()

    def _headers(self):
        if not self.access_token or time.time() - self.issued_at > 7000:
            self._refresh_token()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _request(self, method, url, **kwargs):
        r = requests.request(method, url, headers=self._headers(), **kwargs)

        if r.status_code == 401:
            self._refresh_token()
            r = requests.request(method, url, headers=self._headers(), **kwargs)

        if r.status_code >= 400:
            raise RuntimeError(r.text)

        return r.json() if r.text else None

    # ---------------- LEADS ----------------
    def query(self, soql):
        return self._request(
            "GET",
            f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/query",
            params={"q": soql},
        )

    def create_lead(self, payload):
        r = requests.post(
            f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/sobjects/Lead/",
            json=payload,
            headers=self._headers(),
        )

        if r.status_code >= 400:
            raise RuntimeError(r.text)

        return {"id": r.headers["Location"].split("/")[-1]}

    def update_lead(self, lead_id, payload):
        self._request(
            "PATCH",
            f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/sobjects/Lead/{lead_id}",
            json=payload,
        )

    def delete_lead(self, lead_id):
        self._request(
            "DELETE",
            f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/sobjects/Lead/{lead_id}",
        )

    # ---------------- SOAP CONVERSION ----------------
    def convert_lead(self, lead_id: str) -> dict:
        # REST idempotency check
        lead = self._request(
            "GET",
            f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/sobjects/Lead/{lead_id}",
        )

        if lead.get("IsConverted"):
            return {
                "lead_id": lead_id,
                "status": "Converted",
                "idempotent": True,
            }

        url = f"{SF_INSTANCE_URL}/services/Soap/u/{SF_API_VERSION}"

        soap = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:urn="urn:partner.soap.sforce.com">
          <soapenv:Header>
            <urn:SessionHeader>
              <urn:sessionId>{self.access_token}</urn:sessionId>
            </urn:SessionHeader>
          </soapenv:Header>
          <soapenv:Body>
            <urn:convertLead>
              <urn:leadConverts>
                <urn:leadId>{lead_id}</urn:leadId>
                <urn:convertedStatus>Qualified</urn:convertedStatus>
                <urn:doNotCreateOpportunity>true</urn:doNotCreateOpportunity>
              </urn:leadConverts>
            </urn:convertLead>
          </soapenv:Body>
        </soapenv:Envelope>
        """

        for attempt in range(3):
            r = requests.post(
                url,
                data=soap,
                headers={"Content-Type": "text/xml", "SOAPAction": "convertLead"},
            )

            root = ET.fromstring(r.text)
            success = root.find(".//{urn:partner.soap.sforce.com}success")

            if success is not None and success.text == "true":
                return {"lead_id": lead_id, "status": "Converted", "idempotent": False}

            time.sleep(2 ** attempt)

        # final REST check
        lead = self._request(
            "GET",
            f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/sobjects/Lead/{lead_id}",
        )

        if lead.get("IsConverted"):
            return {
                "lead_id": lead_id,
                "status": "Converted",
                "idempotent": True,
            }

        raise RuntimeError("Lead conversion failed after retries")
