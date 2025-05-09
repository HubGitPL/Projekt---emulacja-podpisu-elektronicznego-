"""
GUI implementation for the PAdES signature application.
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QFileDialog, 
                            QTabWidget, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from pdf_handler import sign_pdf, verify_pdf_signature
from crypto import decrypt_private_key
import os

class SignatureAppWindow(QMainWindow):
    """
    Main window for the PAdES signature application.
    """
    def __init__(self, usb_detector):
        super().__init__()
        self.setWindowTitle("PAdES Signature Application")
        self.setMinimumSize(600, 500)
        
        # Store USB detector reference
        self.usb_detector = usb_detector
        
        # Connect USB detector signals
        self.usb_detector.usb_connected.connect(self.handle_usb_connected)
        self.usb_detector.usb_disconnected.connect(self.handle_usb_disconnected)
        self.usb_detector.status_update.connect(self.handle_status_update)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.sign_tab = QWidget()
        self.verify_tab = QWidget()
        
        self.tabs.addTab(self.sign_tab, "Sign Document")
        self.tabs.addTab(self.verify_tab, "Verify Signature")
        
        # Setup tabs
        self.setup_sign_tab()
        self.setup_verify_tab()
        
        # Status bar at the bottom
        self.status_layout = QHBoxLayout()
        self.key_status = QLabel("Key Status: Not Loaded")
        self.usb_status = QLabel("USB Status: No USB with key detected")
        self.status_layout.addWidget(self.key_status)
        self.status_layout.addWidget(self.usb_status)
        
        # Add widgets to main layout
        layout.addWidget(self.tabs)
        layout.addLayout(self.status_layout)
        
        # Initialize state
        self.private_key = None
        self.current_usb_path = None
        self.encrypted_key_data = None
    
    def handle_usb_connected(self, usb_path, encrypted_key_data):
        """
        Handle USB drive connection with private key.
        
        Args:
            usb_path (str): Path to the USB drive
            encrypted_key_data (bytes): Encrypted private key data
        """
        self.current_usb_path = usb_path
        self.encrypted_key_data = encrypted_key_data
        self.usb_status.setText(f"USB Status: Key detected on {usb_path}")
        self.usb_status.setStyleSheet("color: green;")
        
        # Auto-fill private key path
        key_path = os.path.join(usb_path, "private_key.enc")
        self.private_key_path.setText(key_path)
        
        # Show PIN input dialog
        QMessageBox.information(self, "USB Key Detected", 
                              "Private key detected on USB drive. Please enter your PIN to use it.")
    
    def handle_usb_disconnected(self):
        """
        Handle USB drive disconnection.
        """
        self.current_usb_path = None
        self.encrypted_key_data = None
        self.usb_status.setText("USB Status: No USB with key detected")
        self.usb_status.setStyleSheet("color: red;")
        self.private_key = None
        self.key_status.setText("Key Status: Not Loaded")
        
        # Clear private key path if it was from USB
        if self.private_key_path.text().startswith("/Volumes/"):  # macOS USB path
            self.private_key_path.clear()
        
        QMessageBox.warning(self, "USB Disconnected", 
                          "USB drive with private key has been disconnected. "
                          "Please reconnect it to sign documents.")
    
    def handle_status_update(self, message):
        """
        Handle status updates from USB detector.
        
        Args:
            message (str): Status message
        """
        # Update status bar with the message
        self.statusBar().showMessage(message)
    
    def setup_sign_tab(self):
        """
        Setup the sign document tab.
        """
        layout = QVBoxLayout(self.sign_tab)
        
        # PDF selection
        self.pdf_label = QLabel("Select PDF to sign:")
        self.pdf_path = QLineEdit()
        self.pdf_path.setReadOnly(True)
        self.pdf_browse = QPushButton("Browse")
        self.pdf_browse.clicked.connect(self.browse_pdf)
        
        pdf_layout = QHBoxLayout()
        pdf_layout.addWidget(self.pdf_path)
        pdf_layout.addWidget(self.pdf_browse)
        
        # Private key selection (read-only, auto-filled from USB)
        self.private_key_label = QLabel("Private key location:")
        self.private_key_path = QLineEdit()
        self.private_key_path.setReadOnly(True)
        
        # PIN input
        self.pin_label = QLabel("Enter PIN:")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.textChanged.connect(self.handle_pin_input)
        
        # Output PDF location
        self.output_label = QLabel("Save signed PDF as:")
        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        self.output_browse = QPushButton("Browse")
        self.output_browse.clicked.connect(self.browse_output)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.output_browse)
        
        # Sign button
        self.sign_button = QPushButton("Sign Document")
        self.sign_button.clicked.connect(self.sign_document)
        self.sign_button.setEnabled(False)  # Disabled until PIN is entered
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add widgets to layout
        layout.addWidget(self.pdf_label)
        layout.addLayout(pdf_layout)
        layout.addWidget(self.private_key_label)
        layout.addWidget(self.private_key_path)
        layout.addWidget(self.pin_label)
        layout.addWidget(self.pin_input)
        layout.addWidget(self.output_label)
        layout.addLayout(output_layout)
        layout.addWidget(self.sign_button)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
    
    def handle_pin_input(self):
        """
        Handle PIN input changes.
        """
        if self.pin_input.text() and self.pdf_path.text() and self.output_path.text():
            self.sign_button.setEnabled(True)
        else:
            self.sign_button.setEnabled(False)
    
    def sign_document(self):
        """
        Sign the selected PDF document.
        """
        pdf_path = self.pdf_path.text()
        output_path = self.output_path.text()
        pin = self.pin_input.text()
        
        # Validate inputs
        if not pdf_path:
            QMessageBox.warning(self, "No PDF Selected", "Please select a PDF document to sign.")
            return
        
        if not output_path:
            QMessageBox.warning(self, "No Output Location", "Please select an output location for the signed PDF.")
            return
        
        if not pin:
            QMessageBox.warning(self, "No PIN Entered", "Please enter your PIN.")
            return
        
        # Check if private key is on USB and USB is still connected
        if not self.current_usb_path or not self.encrypted_key_data:
            QMessageBox.critical(self, "USB Disconnected", 
                               "The USB drive containing your private key has been disconnected. "
                               "Please reconnect it to sign the document.")
            return
        
        try:
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(10)
            
            # Decrypt the private key
            private_key = decrypt_private_key(self.encrypted_key_data, pin)
            self.key_status.setText("Key Status: Loaded")
            self.key_status.setStyleSheet("color: green;")
            
            self.progress_bar.setValue(30)
            
            # Sign the PDF
            sign_pdf(pdf_path, output_path, private_key)
            
            self.progress_bar.setValue(100)
            
            # Hide progress bar after a delay
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))
            
            QMessageBox.information(self, "Success", "Document signed successfully!")
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            error_msg = str(e)
            if "Invalid PIN" in error_msg:
                QMessageBox.critical(self, "Invalid PIN", 
                                   "The PIN you entered is incorrect. Please try again.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to sign document: {error_msg}")
    
    def setup_verify_tab(self):
        """
        Setup the verify signature tab.
        """
        layout = QVBoxLayout(self.verify_tab)
        
        # Signed PDF selection
        self.signed_pdf_label = QLabel("Select signed PDF to verify:")
        self.signed_pdf_path = QLineEdit()
        self.signed_pdf_path.setReadOnly(True)
        self.signed_pdf_browse = QPushButton("Browse")
        self.signed_pdf_browse.clicked.connect(self.browse_signed_pdf)
        
        signed_pdf_layout = QHBoxLayout()
        signed_pdf_layout.addWidget(self.signed_pdf_path)
        signed_pdf_layout.addWidget(self.signed_pdf_browse)
        
        # Public key selection
        self.public_key_label = QLabel("Select public key file:")
        self.public_key_path = QLineEdit()
        self.public_key_path.setReadOnly(True)
        self.public_key_browse = QPushButton("Browse")
        self.public_key_browse.clicked.connect(self.browse_public_key)
        
        public_key_layout = QHBoxLayout()
        public_key_layout.addWidget(self.public_key_path)
        public_key_layout.addWidget(self.public_key_browse)
        
        # Verify button
        self.verify_button = QPushButton("Verify Signature")
        self.verify_button.clicked.connect(self.verify_signature)
        
        # Verification result
        self.verification_result = QLabel("")
        self.verification_result.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(self.signed_pdf_label)
        layout.addLayout(signed_pdf_layout)
        layout.addWidget(self.public_key_label)
        layout.addLayout(public_key_layout)
        layout.addWidget(self.verify_button)
        layout.addWidget(self.verification_result)
        layout.addStretch()
    
    def browse_pdf(self):
        """
        Open file dialog to select PDF document to sign.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF Document", "", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_path.setText(file_path)
            # Auto-suggest output path
            suggested_output = file_path.replace(".pdf", "_signed.pdf")
            self.output_path.setText(suggested_output)
    
    def browse_output(self):
        """
        Open file dialog to select output location for signed PDF.
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Signed PDF As", "", "PDF Files (*.pdf)")
        if file_path:
            if not file_path.endswith(".pdf"):
                file_path += ".pdf"
            self.output_path.setText(file_path)
    
    def browse_signed_pdf(self):
        """
        Open file dialog to select signed PDF document to verify.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Signed PDF Document", "", "PDF Files (*.pdf)")
        if file_path:
            self.signed_pdf_path.setText(file_path)
            self.verification_result.setText("")
    
    def browse_public_key(self):
        """
        Open file dialog to select public key file.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Public Key File", "", "PEM Files (*.pem)")
        if file_path:
            self.public_key_path.setText(file_path)
            self.verification_result.setText("")
    
    def verify_signature(self):
        """
        Verify the signature of the selected PDF document.
        """
        pdf_path = self.signed_pdf_path.text()
        public_key_path = self.public_key_path.text()
        
        # Validate inputs
        if not pdf_path:
            QMessageBox.warning(self, "No PDF Selected", "Please select a signed PDF document to verify.")
            return
        
        if not public_key_path:
            QMessageBox.warning(self, "No Public Key", "Please select the public key file.")
            return
        
        try:
            # Load public key
            with open(public_key_path, 'rb') as f:
                public_key_data = f.read()
            
            # Verify the signature
            try:
                is_valid = verify_pdf_signature(pdf_path, public_key_data)
                
                if is_valid:
                    self.verification_result.setText("✅ Signature is valid!")
                    self.verification_result.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.verification_result.setText("❌ Signature is invalid!")
                    self.verification_result.setStyleSheet("color: red; font-weight: bold;")
                    QMessageBox.warning(self, "Invalid Signature", 
                                       "The signature could not be verified. This might be because:\n\n"
                                       "1. The document was modified after signing\n"
                                       "2. The public key doesn't match the private key used to sign\n"
                                       "3. The signature was corrupted or improperly embedded")
            except ValueError as ve:
                self.verification_result.setText(f"❌ Verification Error: {str(ve)}")
                self.verification_result.setStyleSheet("color: red; font-weight: bold;")
                QMessageBox.critical(self, "Verification Error", 
                                    f"Error during verification: {str(ve)}\n\n"
                                    "Make sure you're using the correct public key that corresponds "
                                    "to the private key used for signing.")
            
        except Exception as e:
            self.verification_result.setText(f"Error: {str(e)}")
            self.verification_result.setStyleSheet("color: red;")
            QMessageBox.critical(self, "File Error", 
                               f"Error reading files: {str(e)}\n\n"
                               "Make sure the public key file is in the correct PEM format.") 