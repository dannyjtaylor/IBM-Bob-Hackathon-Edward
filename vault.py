"""
Edward Password Vault Module
Local encrypted password manager - never sends data to external APIs
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from cryptography.fernet import Fernet
import base64
import hashlib

from config import VAULT_PATH

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PasswordVault:
    """
    Encrypted local password vault.
    All data stays on the local machine - never sent to external APIs.
    """
    
    def __init__(self, master_password: str, vault_path: Optional[Path] = None):
        """
        Initialize password vault.
        
        Args:
            master_password: Master password for encryption
            vault_path: Path to vault database (defaults to config)
        """
        self.vault_path = vault_path or VAULT_PATH
        self.master_password = master_password
        self.cipher = self._create_cipher(master_password)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Password vault initialized: {self.vault_path}")
    
    def _create_cipher(self, master_password: str) -> Fernet:
        """
        Create encryption cipher from master password.
        
        Args:
            master_password: Master password
            
        Returns:
            Fernet cipher instance
        """
        # Derive key from master password
        key = hashlib.pbkdf2_hmac(
            'sha256',
            master_password.encode(),
            b'edward_salt',  # In production, use random salt stored separately
            100000
        )
        key_base64 = base64.urlsafe_b64encode(key)
        return Fernet(key_base64)
    
    def _init_database(self):
        """Initialize vault database schema"""
        with sqlite3.connect(self.vault_path) as conn:
            cursor = conn.cursor()
            
            # Create passwords table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password_encrypted BLOB NOT NULL,
                    notes_encrypted BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(service, username)
                )
            """)
            
            conn.commit()
            logger.info("Vault database initialized")
    
    def add_password(self, service: str, username: str, password: str, notes: str = "") -> bool:
        """
        Add or update a password entry.
        
        Args:
            service: Service name (e.g., "Gmail", "GitHub")
            username: Username or email
            password: Password to store
            notes: Optional notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt password and notes
            password_encrypted = self.cipher.encrypt(password.encode())
            notes_encrypted = self.cipher.encrypt(notes.encode()) if notes else None
            
            with sqlite3.connect(self.vault_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO passwords 
                    (service, username, password_encrypted, notes_encrypted, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (service, username, password_encrypted, notes_encrypted))
                
                conn.commit()
            
            logger.info(f"Password added/updated for {service}/{username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add password: {e}")
            return False
    
    def get_password(self, service: str, username: str) -> Optional[Dict[str, str]]:
        """
        Retrieve a password entry.
        
        Args:
            service: Service name
            username: Username
            
        Returns:
            Dictionary with password and notes, or None if not found
        """
        try:
            with sqlite3.connect(self.vault_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT password_encrypted, notes_encrypted
                    FROM passwords
                    WHERE service = ? AND username = ?
                """, (service, username))
                
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # Decrypt password and notes
                password = self.cipher.decrypt(row[0]).decode()
                notes = self.cipher.decrypt(row[1]).decode() if row[1] else ""
                
                return {
                    "service": service,
                    "username": username,
                    "password": password,
                    "notes": notes
                }
                
        except Exception as e:
            logger.error(f"Failed to retrieve password: {e}")
            return None
    
    def list_entries(self) -> List[Dict[str, str]]:
        """
        List all password entries (without decrypting passwords).
        
        Returns:
            List of dictionaries with service and username
        """
        try:
            with sqlite3.connect(self.vault_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT service, username, created_at, updated_at
                    FROM passwords
                    ORDER BY service, username
                """)
                
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        "service": row[0],
                        "username": row[1],
                        "created_at": row[2],
                        "updated_at": row[3]
                    })
                
                return entries
                
        except Exception as e:
            logger.error(f"Failed to list entries: {e}")
            return []
    
    def delete_password(self, service: str, username: str) -> bool:
        """
        Delete a password entry.
        
        Args:
            service: Service name
            username: Username
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.vault_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM passwords
                    WHERE service = ? AND username = ?
                """, (service, username))
                
                conn.commit()
            
            logger.info(f"Password deleted for {service}/{username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete password: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Test vault (use a strong master password in production)
    vault = PasswordVault(master_password="test_master_password_123")
    
    # Add password
    vault.add_password("Gmail", "user@example.com", "super_secret_password", "Personal email")
    
    # Retrieve password
    entry = vault.get_password("Gmail", "user@example.com")
    if entry:
        print(f"Retrieved: {entry}")
    
    # List all entries
    entries = vault.list_entries()
    print(f"Total entries: {len(entries)}")
    for e in entries:
        print(f"  - {e['service']}/{e['username']}")

# Made with Bob
