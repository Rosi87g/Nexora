# app/utils/security.py
from passlib.context import CryptContext

# SINGLE GLOBAL INSTANCE — used by the WHOLE APPLICATION
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12   # you can tune this later (12-14 is good balance 2025-2026)
)