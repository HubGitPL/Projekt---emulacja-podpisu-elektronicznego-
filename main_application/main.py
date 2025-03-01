import os
import hashlib
import getpass
from PyPDF2 import PdfReader, PdfWriter
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Signature import pkcs1_15

def derive_key_from_pin(pin: str) -> bytes:
    return hashlib.sha256(pin.encode()).digest()

# Load and decrypt private key from USB
def load_private_key(usb_path: str, pin: str):
    private_key_path = os.path.join(usb_path, "private_key.enc")
    if not os.path.exists(private_key_path):
        raise FileNotFoundError("Encrypted private key not found!")
    
    aes_key = derive_key_from_pin(pin)
    with open(private_key_path, "rb") as f:
        data = f.read()
    
    first16bytes, ciphertext = data[:16], data[16:]
    cipher = AES.new(aes_key, AES.MODE_CBC, first16bytes)
    private_key = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return RSA.import_key(private_key)

# Sign a PDF file
def sign_pdf(pdf_path: str, private_key: RSA.RsaKey, output_path: str):
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    hash_value = hashlib.sha256(pdf_data).digest()
    signature = pkcs1_15.new(private_key).sign(hash_value)
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    writer.add_metadata({"/Signature": signature.hex()})
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"PDF signed successfully: {output_path}")

def try_load_private_key(usb_path, pin):
    try:
        private_key = load_private_key(usb_path, pin)
        print("Private key loaded successfully.")
        return private_key
    except Exception as e:
        print(f"Error loading private key: {e}")
        return None

# Main function
def main():
    usb_path = input("Enter USB drive path: ")
    if not os.path.exists(usb_path):
        print("Error: USB path not found!")
        return
    
    pin = getpass.getpass("Enter your PIN: ")
    
    private_key = try_load_private_key(usb_path, pin)
    
    pdf_path = input("Enter PDF file path: ")
    if not os.path.exists(pdf_path):
        print("Error: PDF file not found!")
        return
    
    output_path = "signed_document.pdf"
    sign_pdf(pdf_path, private_key, output_path)
    print("Signing process complete.")

if __name__ == "__main__":
    main()
