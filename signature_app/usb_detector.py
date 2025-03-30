"""
USB drive detection module.
"""
import os
import time
import psutil
from PyQt5.QtCore import QThread, pyqtSignal

class USBDetector(QThread):
    """
    Thread for monitoring USB drive connections and disconnections.
    """
    usb_connected = pyqtSignal(str)
    usb_disconnected = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.connected_drives = self.get_removable_drives()
    
    def run(self):
        """
        Main thread loop for monitoring USB drives.
        """
        while self.running:
            current_drives = self.get_removable_drives()
            
            # Check for new drives
            for drive in current_drives:
                if drive not in self.connected_drives:
                    # Check if it has the private key file
                    if os.path.exists(os.path.join(drive, "private_key.enc")):
                        self.usb_connected.emit(drive)
            
            # Check for removed drives
            for drive in self.connected_drives:
                if drive not in current_drives:
                    self.usb_disconnected.emit()
            
            self.connected_drives = current_drives
            time.sleep(1)
    
    def get_removable_drives(self):
        """
        Get a list of removable drives.
        
        Returns:
            list: List of drive paths
        """
        drives = []
        
        for partition in psutil.disk_partitions():
            # Check if it's a removable drive
            if 'removable' in partition.opts or 'cdrom' in partition.opts:
                drives.append(partition.mountpoint)
        
        return drives
    
    def stop_monitoring(self):
        """
        Stop the monitoring thread.
        """
        self.running = False
        self.wait()
    
    def start_monitoring(self):
        """
        Start the monitoring thread.
        """
        self.running = True
        self.start() 