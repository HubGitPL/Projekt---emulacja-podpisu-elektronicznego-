"""
USB drive detection module for PAdES signature application.
"""
import os
import time
import psutil
import platform
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

class USBDetector(QThread):
    """
    Thread for monitoring USB drive connections and disconnections.
    Automatically detects and loads private keys from USB drives.
    """
    usb_connected = pyqtSignal(str, bytes)  # Signal with drive path and encrypted key data
    usb_disconnected = pyqtSignal()
    status_update = pyqtSignal(str)  # Signal for status updates
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.system = platform.system()
        self.connected_drives = self.get_removable_drives()
        self.status_update.emit("USB detector initialized")
    
    def run(self):
        """
        Main thread loop for monitoring USB drives.
        """
        # Check for existing drives with private keys when monitoring starts
        for drive in self.connected_drives:
            self.check_drive_for_key(drive)
        
        while self.running:
            current_drives = self.get_removable_drives()
            
            # Check for new drives
            for drive in current_drives:
                if drive not in self.connected_drives:
                    self.status_update.emit(f"New drive detected: {drive}")
                    self.check_drive_for_key(drive)
            
            # Check for removed drives
            for drive in self.connected_drives:
                if drive not in current_drives:
                    self.status_update.emit(f"Drive removed: {drive}")
                    self.usb_disconnected.emit()
            
            self.connected_drives = current_drives
            time.sleep(1)
    
    def check_drive_for_key(self, drive_path):
        """
        Check if a drive contains a private key file and load it if found.
        
        Args:
            drive_path (str): Path to the drive to check
        """
        key_path = os.path.join(drive_path, "private_key.enc")
        if os.path.exists(key_path):
            try:
                with open(key_path, 'rb') as f:
                    encrypted_key_data = f.read()
                self.status_update.emit(f"Private key found on {drive_path}")
                self.usb_connected.emit(drive_path, encrypted_key_data)
            except Exception as e:
                self.status_update.emit(f"Error reading private key: {str(e)}")
    
    def get_removable_drives(self):
        """
        Get a list of removable drives.
        
        Returns:
            list: List of drive paths
        """
        drives = []
        
        if self.system == "Darwin":  # macOS
            try:
                if os.path.exists("/Volumes"):
                    volumes = os.listdir("/Volumes")
                    for volume in volumes:
                        volume_path = os.path.join("/Volumes", volume)
                        
                        # Skip if not a mount point
                        if not os.path.ismount(volume_path):
                            continue
                            
                        # Skip system volumes and Time Machine backups
                        if any(x in volume for x in ["Macintosh", "System", "Time Machine", "com.apple"]):
                            continue
                            
                        # Get filesystem info
                        try:
                            st = os.statvfs(volume_path)
                            # Check if volume is writable
                            if (st.f_flag & os.ST_RDONLY) == 0:
                                drives.append(volume_path)
                        except:
                            pass
            except Exception as e:
                self.status_update.emit(f"Error detecting drives: {str(e)}")
        else:
            # For other systems (Windows/Linux), use psutil
            for partition in psutil.disk_partitions():
                if 'removable' in partition.opts or 'cdrom' in partition.opts:
                    drives.append(partition.mountpoint)
        
        return drives
    
    def stop_monitoring(self):
        """
        Stop the monitoring thread.
        """
        self.running = False
        self.wait()
        self.status_update.emit("USB monitoring stopped")
    
    def start_monitoring(self):
        """
        Start the monitoring thread.
        """
        self.running = True
        self.start()
        self.status_update.emit("USB monitoring started") 