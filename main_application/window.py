# window.py
import tkinter as tk
from tkinter import filedialog, messagebox
from document_signer import DocumentSigner
import os

class Window:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("PAdES Signature Application")
        self.window.geometry("500x250")
        self.signer = DocumentSigner()
        self.selected_file = None

        self._setup_usb_components()
        self._setup_pin_components()
        self._setup_file_components()
        self._setup_sign_button()
        self._setup_status_label()

        self.window.mainloop()

    def _setup_usb_components(self):
        self.usb_label = tk.Label(self.window, text="Enter USB drive path:")
        self.usb_label.pack()
        self.usb_entry = tk.Entry(self.window)
        self.usb_entry.pack()

    def _setup_pin_components(self):
        self.pin_label = tk.Label(self.window, text="Enter PIN:")
        self.pin_label.pack()
        self.pin_entry = tk.Entry(self.window, show="*")
        self.pin_entry.pack()

    def _setup_file_components(self):
        self.file_label = tk.Label(self.window, text="Select PDF File:")
        self.file_label.pack()
        self.file_button = tk.Button(self.window, text="Browse", command=self._browse_file)
        self.file_button.pack()

    def _browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        self.selected_file = file_path if file_path else None

    def _setup_sign_button(self):
        self.sign_button = tk.Button(self.window, text="Sign Document", command=self._sign_document)
        self.sign_button.pack()

    def _sign_document(self):
        usb_path = self.usb_entry.get()
        pin = self.pin_entry.get()
        pdf_path = self.selected_file

        if not os.path.exists(usb_path):
            messagebox.showerror("Error", "USB path not found!")
            return
        if not pdf_path:
            messagebox.showerror("Error", "No PDF file selected!")
            return

        self._process_signing(usb_path, pin, pdf_path)

    def _process_signing(self, usb_path, pin, pdf_path):
        try:
            self.signer.load_private_key(usb_path, pin)
            output_path = "signed_document.pdf"
            self.signer.sign_pdf(pdf_path, output_path)
            self.status_label.config(text="Status: PDF Signed Successfully", fg="green")
            messagebox.showinfo("Success", "PDF signed successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Status: Error in signing", fg="red")

    def _setup_status_label(self):
        self.status_label = tk.Label(self.window, text="Status: Waiting for input", fg="blue")
        self.status_label.pack()