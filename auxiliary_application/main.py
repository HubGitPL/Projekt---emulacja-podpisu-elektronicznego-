import os
import hashlib
import tkinter as tk
from tkinter import messagebox
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

class Window:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Auxiliary Application")
        self.window.geometry("400x200")
        self.window.resizable(False, False)
        self.key_pair_generator = KeyPairGenerator()

        self.pin_label = tk.Label(self.window, text="Enter a secure PIN:")
        self.pin_label.pack()

        self.pin_entry = tk.Entry(self.window, show="*")
        self.pin_entry.pack()

        self.usb_path_label = tk.Label(self.window, text="Enter USB drive path:")
        self.usb_path_label.pack()

        self.usb_path_entry = tk.Entry(self.window)
        self.usb_path_entry.pack()

        self.submit_button = tk.Button(self.window, text="Submit", command=self.on_submit)
        self.submit_button.pack()

        self.window.mainloop()

    def on_submit(self):
        pin = self.pin_entry.get()
        usb_path = self.usb_path_entry.get()

        self.key_pair_generator.aes_key = self.key_pair_generator.derive_key_from_pin(pin)
        self.key_pair_generator.private_key, self.key_pair_generator.public_key = self.key_pair_generator.generate_rsa_keys()
        self.key_pair_generator.encrypted_private_key = self.key_pair_generator.encrypt_private_key()
        self.key_pair_generator.save_keys(usb_path)

        messagebox.showinfo("Success", "Keys saved successfully!")

        self.usb_path_entry.delete(0, tk.END)
        self.pin_entry.delete(0, tk.END)



class KeyPairGenerator:
    def __init__(self):
        self.aes_key = None
        self.private_key = None
        self.public_key = None
        self.encrypted_private_key = None

    # Step 1: Get user PIN and derive AES key
    def derive_key_from_pin(self, pin: str) -> bytes:
        return hashlib.sha256(pin.encode()).digest()

    # Step 2: Generate RSA Key Pair
    def generate_rsa_keys(self):
        key = RSA.generate(4096)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        return private_key, public_key

    # Step 3: Encrypt private key with AES-256
    def encrypt_private_key(self) -> bytes:
        cipher = AES.new(self.aes_key, AES.MODE_CBC)
        ciphertext = cipher.encrypt(pad(self.private_key, AES.block_size))
        return cipher.iv + ciphertext  # Prepend IV for decryption

    # Step 4: Save keys to disk

    def save_keys(self, usb_path: str):
        private_key_path = os.path.join(usb_path, "private_key.enc")
        public_key_path = "public_key.pem"

        self._write_key_to_file(private_key_path, self.encrypted_private_key)
        self._write_key_to_file(public_key_path, self.public_key)
        
        print(f"Private key saved to USB: {private_key_path}")
        print(f"Public key saved locally: {public_key_path}")

    def _write_key_to_file(self, file_path: str, data: bytes):
        with open(file_path, "wb") as f:
            f.write(data)


def main():
    Window()

if __name__ == "__main__":
    main()
