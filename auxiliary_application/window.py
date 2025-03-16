import os
import tkinter as tk
from tkinter import filedialog, messagebox
from document_signer import DocumentSigner

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