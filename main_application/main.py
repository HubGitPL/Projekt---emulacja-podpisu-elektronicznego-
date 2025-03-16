import os
import hashlib
import getpass
import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Hash import SHA256
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

        hash_value = SHA256.new(pdf_data)
        signature = pkcs1_15.new(self.private_key).sign(hash_value)

        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata({"/Signature": signature.hex()})

        with open(output_path, "wb") as f:
            writer.write(f)
        print(f"PDF signed successfully: {output_path}")

class Window:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("PAdES Signature Application")
        self.window.geometry("500x250")
        self.signer = DocumentSigner()

        self.usb_label = tk.Label(self.window, text="Enter USB drive path:")
        self.usb_label.pack()
        self.usb_entry = tk.Entry(self.window)
        self.usb_entry.pack()

        self.pin_label = tk.Label(self.window, text="Enter PIN:")
        self.pin_label.pack()
        self.pin_entry = tk.Entry(self.window, show="*")
        self.pin_entry.pack()

        self.file_label = tk.Label(self.window, text="Select PDF File:")
        self.file_label.pack()
        self.file_button = tk.Button(self.window, text="Browse", command=self.browse_file)
        self.file_button.pack()

        self.sign_button = tk.Button(self.window, text="Sign Document", command=self.sign_document)
        self.sign_button.pack()

        self.status_label = tk.Label(self.window, text="Status: Waiting for input", fg="blue")
        self.status_label.pack()

        self.window.mainloop()

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        self.selected_file = file_path if file_path else None

    def sign_document(self):
        usb_path = self.usb_entry.get()
        pin = self.pin_entry.get()
        pdf_path = self.selected_file

        if not os.path.exists(usb_path):
            messagebox.showerror("Error", "USB path not found!")
            return
        if not pdf_path:
            messagebox.showerror("Error", "No PDF file selected!")
            return

        try:
            self.signer.load_private_key(usb_path, pin)
            output_path = "signed_document.pdf"
            self.signer.sign_pdf(pdf_path, output_path)
            self.status_label.config(text="Status: PDF Signed Successfully", fg="green")
            messagebox.showinfo("Success", "PDF signed successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Status: Error in signing", fg="red")

def main():
    Window()

if __name__ == "__main__":
    main()
