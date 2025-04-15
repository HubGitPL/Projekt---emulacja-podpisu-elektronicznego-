# Network Security Project 2025

## PAdES Qualified Electronic Signature Emulation Tool

### Project Description

This project implements a software tool for emulating qualified electronic signatures. The application enables users to securely sign PDF documents using an RSA key stored on a hardware device (USB drive), with additional AES encryption protection.

### Key Features

- RSA-4096 digital signatures
- AES-256 encrypted private key storage
- Automatic USB drive detection
- PIN-protected key access
- PDF document signing and verification
- User-friendly GUI interface

### Technologies

#### Programming Language

- Python

#### Cryptographic Algorithms

- RSA-4096 for digital signatures
- AES-256 for key encryption
- SHA-256 for hashing
- PBKDF2 for key derivation

#### Libraries

- PyQt5 for GUI
- cryptography for cryptographic operations
- PyPDF2 for PDF handling
- psutil for system monitoring

### Installation and Configuration

#### Prerequisites

- Python
- pip

#### Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/HubGitPL/Projekt---emulacja-podpisu-elektronicznego-
cd Projekt---emulacja-podpisu-elektronicznego-
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Run the key generator:

```bash
python key_generator/main.py
```

4. Run the signature application:

```bash
python signature_app/main.py
```

### Usage

#### Key Generation

1. Launch the key generator application
2. Enter a secure PIN (minimum 6 digits)
3. Select USB drive for private key storage
4. Select location for public key storage
5. Generate keys

#### Document Signing

1. Launch the signature application
2. Insert USB drive with private key
3. Enter PIN when prompted
4. Select PDF document to sign
5. Choose output location
6. Sign document

#### Signature Verification

1. Launch the signature application
2. Select signed PDF document
3. Select corresponding public key
4. Verify signature

### Project Structure

```
project/
├── key_generator/
│   ├── main.py
│   ├── gui.py
│   └── crypto.py
├── signature_app/
│   ├── main.py
│   ├── gui.py
│   ├── crypto.py
│   ├── pdf_handler.py
│   └── usb_detector.py
└── requirements.txt
```

### Security Features

- Secure key generation using cryptographically secure random number generator
- PIN-protected private key encryption
- Automatic USB drive detection and monitoring
- Secure signature verification
- Protection against document tampering

### License

MIT License

### Development Team

- [Jan Krupiniewicz](https://github.com/JanKrupiniewicz)
- [Mateusz Fydrych](https://github.com/HubGitPL)

### Contact

Please contact the development team through GitHub.


