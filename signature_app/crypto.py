"""
Cryptographic functions for the signature application.
"""
import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def derive_key_from_pin(pin, salt):
    """
    Derive a 256-bit AES key from the PIN.
    
    Args:
        pin (str): User PIN
        salt (bytes): Salt for key derivation
        
    Returns:
        bytes: Derived key
    """
    # Use PBKDF2 to derive a key from the PIN
    key = hashlib.pbkdf2_hmac('sha256', pin.encode(), salt, 100000, 32)
    return key

def decrypt_private_key(encrypted_data, pin):
    """
    Decrypt the private key using AES-256 with a key derived from the PIN.
    
    Args:
        encrypted_data (bytes): Encrypted private key with salt and IV prepended
        pin (str): User PIN
        
    Returns:
        bytes: Decrypted private key in PEM format
    """
    # Extract salt, IV, and encrypted key
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    encrypted_key = encrypted_data[32:]
    
    # Derive key from PIN
    key = derive_key_from_pin(pin, salt)
    
    # Create AES cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    
    # Decrypt the private key
    padded_data = decryptor.update(encrypted_key) + decryptor.finalize()
    
    # Remove padding
    padding_length = padded_data[-1]
    private_key_pem = padded_data[:-padding_length]
    
    return private_key_pem

def sign_data(data, private_key_pem):
    """
    Sign data using the private key.
    
    Args:
        data (bytes): Data to sign
        private_key_pem (bytes): PEM-encoded private key
        
    Returns:
        bytes: Signature
    """
    print(f"Signing data with private key...")
    print(f"Data to sign (hash) length: {len(data)} bytes")
    print(f"Data to sign (hash): {data.hex()}")
    
    # Load private key
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )
        print(f"Successfully loaded private key: {private_key}")
    except Exception as e:
        print(f"ERROR loading private key: {str(e)}")
        raise
    
    try:
        # Sign the data
        print("Signing with PSS padding, SHA256 hash...")
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        print(f"Signature created successfully, length: {len(signature)} bytes")
        print(f"Signature: {signature.hex()[:64]}...")
        return signature
    except Exception as e:
        print(f"ERROR during signing: {str(e)}")
        raise

def verify_signature(data, signature, public_key_pem):
    """
    Verify a signature using the public key.
    
    Args:
        data (bytes): Original data
        signature (bytes): Signature to verify
        public_key_pem (bytes): PEM-encoded public key
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    # Load public key
    try:
        public_key = serialization.load_pem_public_key(public_key_pem)
        print(f"Loaded public key: {public_key}")
    except Exception as e:
        print(f"ERROR loading public key in verify_signature: {str(e)}")
        return False
    
    try:
        # Verify the signature
        print(f"Verifying signature with PSS padding, SHA256 hash")
        print(f"Data to verify (hash): {data.hex()[:32]}...")
        print(f"Signature to verify: {signature.hex()[:32]}...")
        
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print("Signature verification SUCCEEDED!")
        return True
    except Exception as e:
        print(f"Signature verification FAILED: {str(e)}")
        return False 