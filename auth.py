import hashlib
import binascii
import os
import json
import uuid
# Try to import from Crypto (alternative name for pycryptodome) first, then fall back to Cryptodome
try:
    from Crypto.PublicKey import RSA
    from Crypto.Signature import pkcs1_15
    from Crypto.Hash import SHA256
except ImportError:
    # Fall back to Cryptodome if Crypto is not available
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Signature import pkcs1_15
    from Cryptodome.Hash import SHA256
from typing import Dict, Tuple, Optional, Any


class AuthenticationSystem:
    """
    Authentication system for supply chain actors using public/private key cryptography
    """
    def __init__(self):
        self.registered_users = {}  # username -> {public_key, role, organization}
    
    def generate_key_pair(self) -> Tuple[str, str]:
        """
        Generate a new RSA key pair
        
        :return: Tuple of (private_key_string, public_key_string)
        """
        key = RSA.generate(2048)
        private_key = key.export_key().decode('utf-8')
        public_key = key.publickey().export_key().decode('utf-8')
        return private_key, public_key
    
    def register_user(self, username: str, public_key: str, role: str, organization: str) -> str:
        """
        Register a new user in the system
        
        :param username: Unique username
        :param public_key: User's public key (PEM format)
        :param role: User's role in supply chain (e.g., 'producer', 'processor', 'distributor', 'retailer')
        :param organization: User's organization name
        :return: User ID
        """
        if username in self.registered_users:
            raise ValueError(f"Username '{username}' already exists")
        
        user_id = str(uuid.uuid4())
        self.registered_users[username] = {
            'user_id': user_id,
            'public_key': public_key,
            'role': role,
            'organization': organization
        }
        return user_id
    
    def sign_data(self, private_key_string: str, data: Dict[str, Any]) -> str:
        """
        Sign data with a private key
        
        :param private_key_string: Private key in PEM format
        :param data: Data to sign
        :return: Base64 encoded signature
        """
        # Convert data to canonical JSON string
        data_string = json.dumps(data, sort_keys=True)
        
        # Import the private key
        private_key = RSA.import_key(private_key_string)
        
        # Create a hash of the data
        h = SHA256.new(data_string.encode('utf-8'))
        
        # Sign the hash with the private key
        signature = pkcs1_15.new(private_key).sign(h)
        
        # Return the signature as base64
        return binascii.hexlify(signature).decode('ascii')
    
    def verify_signature(self, public_key_string: str, data: Dict[str, Any], signature: str) -> bool:
        """
        Verify a signature with a public key
        
        :param public_key_string: Public key in PEM format
        :param data: Original data that was signed
        :param signature: Base64 encoded signature
        :return: True if verification succeeds, False otherwise
        """
        try:
            # Convert data to canonical JSON string (same as in sign_data)
            data_string = json.dumps(data, sort_keys=True)
            
            # Import the public key
            public_key = RSA.import_key(public_key_string)
            
            # Create a hash of the data
            h = SHA256.new(data_string.encode('utf-8'))
            
            # Verify the signature with the public key
            signature_bytes = binascii.unhexlify(signature)
            pkcs1_15.new(public_key).verify(h, signature_bytes)
            
            # If no exception is raised, verification succeeded
            return True
        except (ValueError, TypeError):
            # Verification failed
            return False
    
    def get_user_info(self, username: str) -> Optional[Dict[str, str]]:
        """
        Get information about a registered user
        
        :param username: Username to look up
        :return: User information or None if not found
        """
        return self.registered_users.get(username)
