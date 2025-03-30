"""
Main entry point for the key generator application.
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui import KeyGeneratorWindow

def main():
    """
    Main function to start the key generator application.
    """
    app = QApplication(sys.argv)
    window = KeyGeneratorWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 