"""
Cryptographic functions for the key generator application.
"""
import os
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def generate_rsa_keypair():
    """
    Generate a 4096-bit RSA key pair.
    
    Returns:
        tuple: (private_key, public_key) as PEM-encoded bytes
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096
    )
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem

def derive_key_from_pin(pin, salt=None):
    """
    Derive a 256-bit AES key from the PIN.
    
    Args:
        pin (str): User PIN
        salt (bytes, optional): Salt for key derivation. If None, a new salt is generated.
        
    Returns:
        tuple: (key, salt) where key is the derived key and salt is the salt used
    """
    if salt is None:
        salt = os.urandom(16)
    
    # Use PBKDF2 to derive a key from the PIN
    key = hashlib.pbkdf2_hmac('sha256', pin.encode(), salt, 100000, 32)
    
    return key, salt

def encrypt_private_key(private_key_pem, pin):
    """
    Encrypt the private key using AES-256 with a key derived from the PIN.
    
    Args:
        private_key_pem (bytes): PEM-encoded private key
        pin (str): User PIN
        
    Returns:
        bytes: Encrypted private key with salt and IV prepended
    """
    # Generate salt and derive key
    salt = os.urandom(16)
    key, _ = derive_key_from_pin(pin, salt)
    
    # Generate random IV
    iv = os.urandom(16)
    
    # Create AES cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    
    # Pad the private key to a multiple of 16 bytes (AES block size)
    padded_data = private_key_pem
    padding_length = 16 - (len(private_key_pem) % 16)
    padded_data += bytes([padding_length]) * padding_length
    
    # Encrypt the private key
    encrypted_key = encryptor.update(padded_data) + encryptor.finalize()
    
    # Return salt + IV + encrypted key
    return salt + iv + encrypted_key

def save_public_key(public_key_pem, directory):
    """
    Save the public key to the specified directory.
    
    Args:
        public_key_pem (bytes): PEM-encoded public key
        directory (str): Directory to save the public key
    """
    public_key_path = os.path.join(directory, "public_key.pem")
    with open(public_key_path, 'wb') as f:
        f.write(public_key_pem)

