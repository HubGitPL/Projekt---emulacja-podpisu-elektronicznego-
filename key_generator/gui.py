"""
GUI implementation for the key generator application.
"""
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                            QLabel, QLineEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from crypto import generate_rsa_keypair, encrypt_private_key, save_public_key

class KeyGeneratorWindow(QMainWindow):
    """
    Main window for the key generator application.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Signature Key Generator")
        self.setMinimumSize(500, 300)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # PIN input
        self.pin_label = QLabel("Enter PIN (min 6 digits):")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        
        # Confirm PIN input
        self.confirm_pin_label = QLabel("Confirm PIN:")
        self.confirm_pin_input = QLineEdit()
        self.confirm_pin_input.setEchoMode(QLineEdit.Password)
        
        # Private key storage selection
        self.private_key_label = QLabel("Select folder for private key storage:")
        self.private_key_path = QLineEdit()
        self.private_key_path.setReadOnly(True)
        self.private_key_browse = QPushButton("Browse")
        self.private_key_browse.clicked.connect(self.browse_private_key)
        
        # Local path for public key
        self.public_key_label = QLabel("Select location for public key storage:")
        self.public_key_path = QLineEdit()
        self.public_key_path.setReadOnly(True)
        self.public_key_browse = QPushButton("Browse")
        self.public_key_browse.clicked.connect(self.browse_public_key)
        
        # Generate button
        self.generate_button = QPushButton("Generate Keys")
        self.generate_button.clicked.connect(self.generate_keys)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(self.pin_label)
        layout.addWidget(self.pin_input)
        layout.addWidget(self.confirm_pin_label)
        layout.addWidget(self.confirm_pin_input)
        layout.addWidget(self.private_key_label)
        layout.addWidget(self.private_key_path)
        layout.addWidget(self.private_key_browse)
        layout.addWidget(self.public_key_label)
        layout.addWidget(self.public_key_path)
        layout.addWidget(self.public_key_browse)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.status_label)
        
    def browse_private_key(self):
        """
        Open file dialog to select private key storage location.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Private Key Storage Location")
        if folder:
            self.private_key_path.setText(folder)
    
    def browse_public_key(self):
        """
        Open file dialog to select public key storage location.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Public Key Storage Location")
        if folder:
            self.public_key_path.setText(folder)
    
    def generate_keys(self):
        """
        Generate RSA key pair and store them in the specified locations.
        """
        pin = self.pin_input.text()
        confirm_pin = self.confirm_pin_input.text()
        private_key_path_folder = self.private_key_path.text()
        public_key_path = self.public_key_path.text()
        
        # Validate inputs
        if not pin or len(pin) < 6 or not pin.isdigit():
            QMessageBox.warning(self, "Invalid PIN", "PIN must be at least 6 digits.")
            return
        
        if pin != confirm_pin:
            QMessageBox.warning(self, "PIN Mismatch", "PINs do not match.")
            return
        
        if not private_key_path_folder:
            QMessageBox.warning(self, "No Private Key Location", "Please select a location for the private key.")
            return
        
        if not public_key_path:
            QMessageBox.warning(self, "No Public Key Location", "Please select a location for the public key.")
            return
        
        try:
            # Generate RSA key pair
            self.status_label.setText("Generating RSA key pair...")
            private_key, public_key = generate_rsa_keypair()
            
            # Encrypt private key with PIN
            self.status_label.setText("Encrypting private key...")
            encrypted_private_key = encrypt_private_key(private_key, pin)
            
            # Save private key to selected location
            private_key_file_path = os.path.join(private_key_path_folder, "private_key.enc")
            with open(private_key_file_path, 'wb') as f:
                f.write(encrypted_private_key)
            
            # Save public key to local storage
            save_public_key(public_key, public_key_path)
            
            self.status_label.setText("Keys generated and stored successfully!")
            QMessageBox.information(self, "Success", 
                                   "RSA key pair generated successfully.\n"
                                   f"Private key stored at: {private_key_file_path}\n"
                                   f"Public key stored at: {os.path.join(public_key_path, 'public_key.pem')}")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate keys: {str(e)}") 