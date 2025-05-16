"""
GUI implementation for the key generator application with USB detection.
"""
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QMessageBox,
                             QHBoxLayout, QStatusBar)
from PyQt5.QtCore import Qt
from usb_detector import USBDetector
from crypto import generate_rsa_keypair, encrypt_private_key, save_public_key

sizeX = 600
sizeY = 400

class KeyGeneratorWindow(QMainWindow):
    """
    Main window for the key generator application.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Signature Key Generator")
        self.setMinimumSize(sizeX, sizeY)

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

        # Public key storage selection
        self.public_key_label = QLabel("Select location for public key storage:")
        self.public_key_path = QLineEdit()
        self.public_key_path.setReadOnly(True)
        self.public_key_browse = QPushButton("Browse")
        self.public_key_browse.clicked.connect(self.browse_public_key)

        # Layout for public key selection
        public_key_layout = QHBoxLayout()
        public_key_layout.addWidget(self.public_key_path)
        public_key_layout.addWidget(self.public_key_browse)

        # Generate button
        self.generate_button = QPushButton("Generate Keys")
        self.generate_button.clicked.connect(self.generate_keys)
        self.generate_button.setEnabled(False)

        # Status label for operations
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)

        # USB status indicator
        self.usb_status_layout = QHBoxLayout()
        self.usb_status = QLabel("USB Status: No USB drive detected")
        self.usb_status.setStyleSheet("color: red;")
        self.usb_path_label = QLabel("Path: -")
        self.usb_status_layout.addWidget(self.usb_status)
        self.usb_status_layout.addWidget(self.usb_path_label)
        self.usb_status_layout.addStretch()

        # Add widgets to layout
        layout.addWidget(self.pin_label)
        layout.addWidget(self.pin_input)
        layout.addWidget(self.confirm_pin_label)
        layout.addWidget(self.confirm_pin_input)
        layout.addWidget(self.public_key_label)
        layout.addLayout(public_key_layout)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.status_label)
        layout.addSpacing(20)
        layout.addLayout(self.usb_status_layout)
        layout.addStretch()

        # Create and set up status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # USB detection
        self.usb_detector = USBDetector()
        self.usb_detector.usb_connected.connect(self.on_usb_connected)
        self.usb_detector.usb_disconnected.connect(self.on_usb_disconnected)
        self.usb_detector.status_update.connect(self.update_status)
        self.usb_detector.start_monitoring()
        self.usb_path = None

        # Connect text change events for validation
        self.pin_input.textChanged.connect(self.validate_inputs)
        self.confirm_pin_input.textChanged.connect(self.validate_inputs)
        self.public_key_path.textChanged.connect(self.validate_inputs)

    def validate_inputs(self):
        """
        Validate all inputs and enable/disable the generate button.
        """
        pin = self.pin_input.text()
        confirm_pin = self.confirm_pin_input.text()
        public_key_path = self.public_key_path.text()

        valid = bool(len(pin) >= 6 and pin.isdigit() and
                 pin == confirm_pin and
                 public_key_path and
                 self.usb_path is not None)

        self.generate_button.setEnabled(valid)

    def update_status(self, message):
        """
        Update status bar with a message.
        """
        self.statusBar.showMessage(message)

    def browse_public_key(self):
        """
        Open file dialog to select public key storage location.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Public Key Storage Location")
        if folder:
            self.public_key_path.setText(folder)

    def on_usb_connected(self, path):
        """
        Handle USB drive connection.
        """
        self.usb_path = path
        self.usb_status.setText("USB Status: USB drive detected")
        self.usb_status.setStyleSheet("color: green; font-weight: bold;")
        self.usb_path_label.setText(f"Path: {path}")
        self.update_status(f"USB drive detected at {path}")
        self.validate_inputs()

    def on_usb_disconnected(self):
        """
        Handle USB drive disconnection.
        """
        self.usb_path = None
        self.usb_status.setText("USB Status: No USB drive detected")
        self.usb_status.setStyleSheet("color: red;")
        self.usb_path_label.setText("Path: -")
        self.update_status("USB drive disconnected")
        self.validate_inputs()

    def generate_keys(self):
        """
        Generate RSA key pair and store them in the specified locations.
        """
        pin = self.pin_input.text()
        confirm_pin = self.confirm_pin_input.text()
        public_key_path = self.public_key_path.text()

        # Validate inputs
        if not pin or len(pin) < 6 or not pin.isdigit():
            QMessageBox.warning(self, "Invalid PIN", "PIN must be at least 6 digits.")
            return

        if pin != confirm_pin:
            QMessageBox.warning(self, "PIN Mismatch", "PINs do not match.")
            return

        if not self.usb_path:
            QMessageBox.warning(self, "No USB Detected", "Please insert a USB drive.")
            return

        if not public_key_path:
            QMessageBox.warning(self, "No Public Key Location", "Please select a location for the public key.")
            return

        try:
            # Generate RSA key pair
            self.status_label.setText("Generating RSA key pair...")
            self.update_status("Generating RSA key pair...")
            private_key, public_key = generate_rsa_keypair()

            # Encrypt private key with PIN
            self.status_label.setText("Encrypting private key...")
            self.update_status("Encrypting private key...")
            encrypted_private_key = encrypt_private_key(private_key, pin)

            # Save private key to USB drive
            private_key_file_path = os.path.join(self.usb_path, "private_key.enc")
            self.update_status(f"Saving private key to {private_key_file_path}...")
            with open(private_key_file_path, 'wb') as f:
                f.write(encrypted_private_key)

            # Save public key to local storage
            public_key_file_path = os.path.join(public_key_path, "public_key.pem")
            self.update_status(f"Saving public key to {public_key_file_path}...")
            save_public_key(public_key, public_key_path)

            self.status_label.setText("Keys generated and stored successfully!")
            self.update_status("Keys generated and stored successfully")
            QMessageBox.information(self, "Success",
                                    "RSA key pair generated successfully.\n"
                                    f"Private key stored at: {private_key_file_path}\n"
                                    f"Public key stored at: {public_key_file_path}")

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.update_status(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate keys: {str(e)}")

    def closeEvent(self, event):
        """
        Stop the USB detector when closing the application.
        """
        self.usb_detector.stop()
        super().closeEvent(event)
