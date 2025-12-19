from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2id configuration (OWASP recommended)
pwd_hasher = PasswordHasher(
    time_cost=2,       # iterations
    memory_cost=102400, # 100 MB
    parallelism=8,
    hash_len=32,
    salt_len=16,
)

def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False