"""
Main entry point for the signature application.
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui import SignatureAppWindow

def main():
    """
    Main function to start the signature application.
    """
    app = QApplication(sys.argv)
    window = SignatureAppWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 