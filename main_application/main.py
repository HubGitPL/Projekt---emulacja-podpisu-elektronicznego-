import os
import hashlib
import getpass
from PyPDF2 import PdfReader, PdfWriter
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Signature import pkcs1_15


class DocumentSigner:
    def __init__(self):
        self.private_key = None

    def derive_key_from_pin(self, pin: str) -> bytes:
        return hashlib.sha256(pin.encode()).digest()

    def load_private_key(self, usb_path: str, pin: str):
        private_key_path = os.path.join(usb_path, "private_key.enc")
        if not os.path.exists(private_key_path):
            raise FileNotFoundError("Encrypted private key not found!")

        aes_key = self.derive_key_from_pin(pin)
        with open(private_key_path, "rb") as f:
            data = f.read()

        iv, ciphertext = data[:16], data[16:]
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        private_key_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
        self.private_key = RSA.import_key(private_key_data)
        return self.private_key

    def sign_pdf(self, pdf_path: str, output_path: str):
        if not self.private_key:
            raise ValueError("Private key not loaded. Call load_private_key first.")

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        hash_value = hashlib.sha256(pdf_data).digest()
        signature = pkcs1_15.new(self.private_key).sign(hash_value)

        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.add_metadata({"/Signature": signature.hex()})
        with open(output_path, "wb") as f:
            writer.write(f)
        print(f"PDF signed successfully: {output_path}")


class MainApplication:
    def __init__(self):
        self.document_signer = DocumentSigner()

    def run(self):
        usb_path = input("Enter USB drive path: ")
        if not os.path.exists(usb_path):
            print("Error: USB path not found!")
            return

        pin = getpass.getpass("Enter your PIN: ")

        if not self._load_private_key(usb_path, pin):
            return

        pdf_path = input("Enter PDF file path: ")
        if not os.path.exists(pdf_path):
            print("Error: PDF file not found!")
            return

        output_path = "signed_document.pdf"
        try:
            self.document_signer.sign_pdf(pdf_path, output_path)
            print("Signing process complete.")
        except Exception as e:
            print(f"Error signing PDF: {e}")

    def _load_private_key(self, usb_path, pin):
        try:
            self.document_signer.load_private_key(usb_path, pin)
            print("Private key loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading private key: {e}")
            return False


def main():
    app = MainApplication()
    app.run()


if __name__ == "__main__":
    main()