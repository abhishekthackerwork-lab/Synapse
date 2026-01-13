import base64
import json
import httpx

from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from app.core.config import settings
from datetime import datetime, timedelta, UTC

def _vault_http_client():
    return httpx.AsyncClient(
        # Remove verify=False as it's not needed for HTTP
        timeout=10.0,
        # Ensure we are sending valid JSON
        headers={"Content-Type": "application/json"}
    )


class VaultClient:
    def __init__(self):
        self.vault_addr = settings.VAULT_ADDR
        self.role_id = settings.VAULT_ROLE_ID
        self.secret_id = settings.VAULT_SECRET_ID
        self.client_token = None

    async def authenticate(self):

        async with _vault_http_client() as client:
            resp = await client.post(
                f"{self.vault_addr}/v1/auth/approle/login",
                json={"role_id": self.role_id, "secret_id": self.secret_id},
            )
            resp.raise_for_status()
            data = resp.json()
            self.client_token = data["auth"]["client_token"]
            return self.client_token

    async def read_database_creds(self, role_name: str) -> dict:
        """
        Read dynamic DB credentials from Vault database secrets engine.
        """
        if not self.client_token:
            await self.authenticate()

        async with _vault_http_client() as client:
            resp = await client.get(
                f"{self.vault_addr}/v1/database/creds/{role_name}",
                headers={"X-Vault-Token": self.client_token},
            )
            resp.raise_for_status()
            data = resp.json()

            return {
                "username": data["data"]["username"],
                "password": data["data"]["password"],
                "lease_duration": data["lease_duration"],
                "renewable": data["renewable"],
            }


    async def sign_jwt(self, payload: dict) -> str:
        """
        Sign JWT using Vault transit ES256 key.
        Vault returns DER-encoded ECDSA signatures → must convert to JOSE format.
        """
        if not self.client_token:
            await self.authenticate()

        # 1. Build JWT header
        header = {"alg": "ES256", "typ": "JWT", "kid": "jwt_signer_es256"}

        # 2. Base64URL encode header & payload (no padding)
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")

        # 3. Message to sign (header.payload), again base64URL encoded
        signing_input = header_b64 + b"." + payload_b64
        signing_input_b64 = base64.urlsafe_b64encode(signing_input).decode()

        # 4. Ask Vault to sign
        async with _vault_http_client() as client:
            resp = await client.post(
                f"{self.vault_addr}/v1/transit/sign/jwt_signer_es256",
                json={"input": signing_input_b64},
                headers={"X-Vault-Token": self.client_token},
            )
            resp.raise_for_status()
            vault_sig = resp.json()["data"]["signature"].split(":")[2]

        padding = "=" * (-len(vault_sig) % 4)
        der_sig = base64.b64decode(vault_sig + padding)

        # 7. Decode DER → (r, s) big integers
        r, s = decode_dss_signature(der_sig)

        # 8. Convert r and s → 32-byte big endian
        r_bytes = r.to_bytes(32, byteorder="big")
        s_bytes = s.to_bytes(32, byteorder="big")

        # 9. JOSE ES256 signature = r||s
        raw_sig = r_bytes + s_bytes

        # 10. Base64URL encode without padding
        signature_b64 = base64.urlsafe_b64encode(raw_sig).rstrip(b"=").decode()

        # 11. Final JWT
        return f"{header_b64.decode()}.{payload_b64.decode()}.{signature_b64}"

    async def read_kv_secret(self, path: str):
        if not self.client_token:
            await self.authenticate()

        async with _vault_http_client() as client:
            resp = await client.get(
                f"{self.vault_addr}/v1/kv/data/{path}",
                headers={"X-Vault-Token": self.client_token},
            )
            resp.raise_for_status()
            return resp.json()["data"]["data"]


# Global instance of VaultClient
vault_client = VaultClient()

_db_creds = None
_db_creds_expiry: datetime | None = None


async def get_db_credentials():
    global _db_creds, _db_creds_expiry

    now = datetime.now(UTC)

    # Refresh if missing or expiring soon
    if (
        _db_creds is None
        or _db_creds_expiry is None
        or now >= _db_creds_expiry - timedelta(minutes=5)
    ):
        secret = await vault_client.read_database_creds("synapse-app")

        _db_creds = {
            "username": secret["username"],
            "password": secret["password"],
        }

        _db_creds_expiry = now + timedelta(seconds=secret["lease_duration"])

    return _db_creds
