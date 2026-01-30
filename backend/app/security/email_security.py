# backend/app/utils/email_security.py
import hashlib
import base64
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Load from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY missing in .env - Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")

fernet = Fernet(ENCRYPTION_KEY.encode())

class EmailSecurity:
    """
    Handles email encryption and hashing
    - Encrypted email: Can be decrypted for sending emails
    - Email hash: For fast lookups and uniqueness checks (SHA-256)
    """
    
    @staticmethod
    def encrypt_email(email: str) -> str:
        """
        Encrypt email using Fernet (reversible)
        Returns base64-encoded encrypted string
        """
        email_bytes = email.encode('utf-8')
        encrypted = fernet.encrypt(email_bytes)
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_email(encrypted_email: str) -> str:
        """
        Decrypt email back to plain text
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_email.encode('utf-8'))
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt email: {str(e)}")
    
    @staticmethod
    def hash_email(email: str) -> str:
        """
        Create deterministic hash for lookups (SHA-256)
        ✅ Same email = same hash (unlike bcrypt)
        This is used for database queries
        """
        return hashlib.sha256(email.encode('utf-8')).hexdigest()
    
    @staticmethod
    def prepare_email_for_storage(email: str) -> dict:
        """
        Prepare email for database storage
        Returns both encrypted and hashed versions
        
        Example:
        >>> data = EmailSecurity.prepare_email_for_storage("user@example.com")
        >>> data
        {
            'email_encrypted': 'Z0FBQUFBQm...',
            'email_hash': 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'
        }
        """
        email_clean = email.lower().strip()
        return {
            'email_encrypted': EmailSecurity.encrypt_email(email_clean),
            'email_hash': EmailSecurity.hash_email(email_clean)
        }

# Create singleton instance
email_sec = EmailSecurity()