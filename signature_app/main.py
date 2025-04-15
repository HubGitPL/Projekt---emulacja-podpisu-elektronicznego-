"""
Main entry point for the signature application.
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui import SignatureAppWindow
from usb_detector import USBDetector

def main():
    """
    Main function to start the signature application.
    """
    app = QApplication(sys.argv)
    
    # Initialize USB detector
    usb_detector = USBDetector()
    
    # Create and show main window
    window = SignatureAppWindow(usb_detector)
    window.show()
    
    # Start USB monitoring
    usb_detector.start_monitoring()
    
    # Clean up when application exits
    app.aboutToQuit.connect(usb_detector.stop_monitoring)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 