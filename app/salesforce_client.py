import time
import requests
from app.config import (
    SF_CLIENT_ID,
    SF_CLIENT_SECRET,
    SF_REFRESH_TOKEN,
    SF_INSTANCE_URL,
    SF_TOKEN_URL,
    SF_API_VERSION,
)


class SalesforceClient:
    def __init__(self):
        self.access_token = None
        self.issued_at = 0

    # ---------------- AUTH ----------------
    def _refresh_token(self):
        resp = requests.post(
            SF_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": SF_CLIENT_ID,
                "client_secret": SF_CLIENT_SECRET,
                "refresh_token": SF_REFRESH_TOKEN,
            },
        )

        if resp.status_code != 200:
            raise RuntimeError("Failed to refresh Salesforce token")

        data = resp.json()
        self.access_token = data["access_token"]
        self.issued_at = time.time()

    def _headers(self):
        if not self.access_token:
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
        url = f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/query"
        return self._request("GET", url, params={"q": soql})

    def create_lead(self, payload):
        url = f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/sobjects/Lead/"
        r = requests.post(url, json=payload, headers=self._headers())

        if r.status_code == 400 and "DUPLICATES_DETECTED" in r.text:
            data = r.json()[0]
            lead_id = (
                data["duplicateResult"]["matchResults"][0]
                ["matchRecords"][0]["record"]["Id"]
            )
            self.update_lead(lead_id, payload)
            return {"id": lead_id, "duplicate": True}

        if r.status_code >= 400:
            raise RuntimeError(r.text)

        return {"id": r.headers["Location"].split("/")[-1]}

    def update_lead(self, lead_id, payload):
        url = f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/sobjects/Lead/{lead_id}"
        self._request("PATCH", url, json=payload)

    def delete_lead(self, lead_id):
        url = f"{SF_INSTANCE_URL}/services/data/{SF_API_VERSION}/sobjects/Lead/{lead_id}"
        self._request("DELETE", url)

    # ---------------- SOAP CONVERSION ----------------
    def convert_lead(self, lead_id):
        if not self.access_token:
            self._refresh_token()

        url = f"{SF_INSTANCE_URL}/services/Soap/u/{SF_API_VERSION}"

        soap = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                        xmlns:urn="urn:enterprise.soap.sforce.com">
        <soapenv:Header>
            <urn:SessionHeader>
            <urn:sessionId>{self.access_token}</urn:sessionId>
            </urn:SessionHeader>
        </soapenv:Header>
        <soapenv:Body>
            <urn:convertLead>
            <urn:leadConverts>
                <urn:leadId>{lead_id}</urn:leadId>
                <urn:doNotCreateOpportunity>true</urn:doNotCreateOpportunity>
            </urn:leadConverts>
            </urn:convertLead>
        </soapenv:Body>
        </soapenv:Envelope>
        """

        r = requests.post(url, data=soap, headers={"Content-Type": "text/xml"})
        if r.status_code >= 400:
            raise RuntimeError(r.text)

        return True
