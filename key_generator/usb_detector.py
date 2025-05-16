"""
USB drive detection module for the key generator application.
"""
import os
import time
import psutil
import platform
from PyQt5.QtCore import QThread, pyqtSignal

class USBDetector(QThread):
    """
    Thread for monitoring USB drive connections and disconnections.
    Automatically detects USB drives for key storage.
    """
    usb_connected = pyqtSignal(str)  # Signal with drive path
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
        # Check for existing drives when monitoring starts
        for drive in self.connected_drives:
            self.status_update.emit(f"Existing drive detected: {drive}")
            self.usb_connected.emit(drive)
        
        while self.running:
            current_drives = self.get_removable_drives()
            
            # Check for new drives
            for drive in current_drives:
                if drive not in self.connected_drives:
                    self.status_update.emit(f"New drive detected: {drive}")
                    self.usb_connected.emit(drive)
            
            # Check for removed drives
            for drive in self.connected_drives:
                if drive not in current_drives:
                    self.status_update.emit(f"Drive removed: {drive}")
                    self.usb_disconnected.emit()
            
            self.connected_drives = current_drives
            time.sleep(1)
    
    def get_removable_drives(self):
        """
        Get a list of removable drives connected to the system.
        
        On macOS:
        - Checks volumes in /Volumes directory
        - Excludes system volumes, Time Machine backups, and non-writable volumes
        - Verifies mount points and filesystem writability
        
        On Windows/Linux:
        - Uses psutil to detect removable drives and CD-ROMs
        - Identifies drives based on 'removable' or 'cdrom' mount options
        
        Returns:
            list: List of absolute paths to mounted removable drives
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
    
    def stop(self):
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
