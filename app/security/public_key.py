from pathlib import Path

PUBLIC_KEY = Path("app/security/jwt_public_key.pem").read_text()
