from datetime import datetime, timedelta, timezone
from app.security.vault_client import vault_client


async def create_access_token(data: dict, expires_minutes: int):
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)

    payload = {**data, "iat": now.timestamp(), "exp": expire.timestamp()}

    return await vault_client.sign_jwt(payload)

