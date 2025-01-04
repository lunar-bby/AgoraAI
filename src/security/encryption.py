from typing import Tuple, Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey
import base64
import os
import json

class EncryptionManager:
    def __init__(self):
        self.fernet = Fernet(Fernet.generate_key())
        
    def generate_key_pair(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def encrypt_message(self, message: bytes, public_key: rsa.RSAPublicKey) -> bytes:
        return public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def decrypt_message(self, encrypted_message: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
        return private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def symmetric_encrypt(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)
    
    def symmetric_decrypt(self, encrypted_data: bytes) -> bytes:
        return self.fernet.decrypt(encrypted_data)
    
    def generate_key_from_password(
        self,
        password: str,
        salt: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

class SecureChannel:
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
        self.session_key: Optional[bytes] = None
        self.private_key: Optional[rsa.RSAPrivateKey] = None
        self.public_key: Optional[rsa.RSAPublicKey] = None
        self.peer_public_key: Optional[rsa.RSAPublicKey] = None
    
    def initialize(self) -> Dict[str, Any]:
        self.private_key, self.public_key = self.encryption_manager.generate_key_pair()
        self.session_key = os.urandom(32)
        
        return {
            "public_key": self.public_key,
            "session_key": self.session_key
        }
    
    def establish_connection(
        self,
        peer_public_key: rsa.RSAPublicKey,
        encrypted_session_key: bytes
    ) -> None:
        self.peer_public_key = peer_public_key
        self.session_key = self.encryption_manager.decrypt_message(
            encrypted_session_key,
            self.private_key
        )
    
    def encrypt_data(self, data: Dict[str, Any]) -> bytes:
        if not self.session_key or not self.peer_public_key:
            raise ValueError("Secure channel not established")
            
        data_bytes = json.dumps(data).encode()
        encrypted_data = self.encryption_manager.symmetric_encrypt(data_bytes)
        
        return self.encryption_manager.encrypt_message(
            encrypted_data,
            self.peer_public_key
        )
    
    def decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        if not self.session_key or not self.private_key:
            raise ValueError("Secure channel not established")
            
        decrypted_message = self.encryption_manager.decrypt_message(
            encrypted_data,
            self.private_key
        )
        
        decrypted_data = self.encryption_manager.symmetric_decrypt(decrypted_message)
        return json.loads(decrypted_data.decode())

class DataEncryption:
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
        self.keys: Dict[str, bytes] = {}
    
    def encrypt_file(
        self,
        file_path: str,
        key: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        if key is None:
            key = Fernet.generate_key()
        
        with open(file_path, 'rb') as file:
            data = file.read()
            
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data)
        
        return encrypted_data, key
    
    def decrypt_file(
        self,
        encrypted_data: bytes,
        key: bytes
    ) -> bytes:
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data)
    
    def store_key(self, key_id: str, key: bytes) -> None:
        self.keys[key_id] = key
    
    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        return self.keys.get(key_id)
    
    def remove_key(self, key_id: str) -> None:
        self.keys.pop(key_id, None)