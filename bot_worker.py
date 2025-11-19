import subprocess
import time
import os
import cv2
import numpy as np
import pytesseract
import re
from datetime import datetime
from models import db
from models.bot_config import BotConfig, BotLog, BotTimer
from models.user import User


class VMOSCloudBot:
    """VMOSCloud Bot - Automates truck sharing in Last War"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.user = User.query.get(user_id)
        self.config = BotConfig.query.filter_by(user_id=user_id).first()
        
        if not self.config or not self.config.is_configured:
            raise Exception("Bot not configured for this user")
        
        # SSH Tunnel
        self.ssh_tunnel_process = None
        self.adb_connected = False
        
        # Template path
        self.template_path = os.path.join(os.path.dirname(__file__), 'static/templates/rentier_template.png')
        
        # Screen dimensions
        self.screen_width = self.config.screen_width
        self.screen_height = self.config.screen_height
        
        # Device identifier for ADB
        self.device = f'localhost:{self.config.local_adb_port}'
        
        # Fixed coordinates (for 720x1280 screen)
        self.COORDS = {
            # General
            'refresh': (680, 70),  # Refresh/search again button (top right)
            'share': (450, 1100),  # Share button (blue button in LKW details)
            
            # World Chat Mode
            'share_world_channel': (300, 450),  # Select "World" channel in share dialog
            'share_world_confirm': (400, 750),  # Confirm send in world chat
            
            # Alliance Mode
            'share_alliance_channel': (300, 700),  # Select "Alliance" channel in share dialog
            'share_alliance_confirm': (400, 750),  # Confirm send in alliance chat
        }
        
        # OCR regions (L, O, R, U) for reading truck info
        self.OCR_REGIONS = {
            'strength': (200, 950, 300, 1000),  # Truck strength box (left, top, right, bottom)
            'server': (160, 860, 220, 915),  # Server number box
        }
        
        # Remembered trucks (to avoid re-sharing)
        self.shared_trucks = set()
        
        self.log(f"Bot initialized for user {self.user.email}")
    
    def log(self, message, level='info'):
        """Add log entry - simplified for users"""
        # Only log to console in debug mode
        print(f"[BOT {self.user_id}] {message}")
        
        # Simplified messages for user
        user_messages = {
            # Connection
            'Setting up SSH tunnel...': 'Connecting...',
            'SSH tunnel established successfully': 'Connected',
            'Connecting ADB...': 'Connecting to device...',
            'ADB connected successfully': 'Device connected',
            'Bot started successfully!': 'Bot started',
            'Starting main bot loop...': 'Searching for trucks...',
            
            # Cleanup
            'Cleaning up old tunnels...': None,  # Don't show
            'Waiting for tunnel to stabilize...': None,  # Don't show
            'Bot stop signal received, exiting loop': 'Stopping bot...',
            'Cleaning up...': None,  # Don't show
            'Cleanup complete': 'Bot stopped',
            
            # Debug logs - don't show to user
            'Screenshot saved to': None,
            'Template:': None,
            'Screenshot shape:': None,
            'Match confidence:': None,
        }
        
        # Check if we should simplify or skip this message
        user_message = message
        for key, simplified in user_messages.items():
            if message.startswith(key):
                if simplified is None:
                    return  # Skip this log
                user_message = simplified
                break
        
        # Log to database (visible to user)
        BotLog.add_log(self.user_id, level, user_message)
    
    def start(self):
        """Start the bot"""
        try:
            self.log("Starting bot...")
            
            # 1. Setup SSH tunnel
            if not self.setup_ssh_tunnel():
                self.log("Failed to setup SSH tunnel", 'error')
                return False
            
            # 2. Connect ADB
            if not self.connect_adb():
                self.log("Failed to connect ADB", 'error')
                self.cleanup()
                return False
            
            self.log("Bot started successfully!", 'success')
            return True
            
        except Exception as e:
            self.log(f"Error starting bot: {e}", 'error')
            self.cleanup()
            return False
    
    def setup_ssh_tunnel(self):
        """Setup SSH tunnel to VMOSCloud"""
        try:
            self.log("Setting up SSH tunnel...")
            
            # Kill any existing tunnels on this port first
            self.log("Cleaning up old tunnels...")
            subprocess.run(['pkill', '-f', f'{self.config.local_adb_port}:adb-proxy'], 
                         capture_output=True)
            subprocess.run(['adb', 'disconnect', self.device],
                         capture_output=True)
            time.sleep(1)
            
            # Build SSH command
            ssh_cmd = [
                'sshpass',
                '-p', self.config.ssh_key,
                'ssh',
                '-oHostKeyAlgorithms=+ssh-rsa',
                '-oStrictHostKeyChecking=no',
                '-oUserKnownHostsFile=/dev/null',
                self.config.ssh_username,
                '-p', str(self.config.ssh_port),
                '-L', f'{self.config.local_adb_port}:adb-proxy:{self.config.adb_proxy_port}',
                '-Nf'
            ]
            
            # Execute SSH tunnel
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                self.log(f"SSH tunnel failed: {result.stderr}", 'error')
                return False
            
            # Wait longer for tunnel to establish
            self.log("Waiting for tunnel to stabilize...")
            time.sleep(5)
            
            self.log("SSH tunnel established successfully")
            return True
            
        except Exception as e:
            self.log(f"SSH tunnel error: {e}", 'error')
            return False
    
    def connect_adb(self):
        """Connect ADB to VMOSCloud device"""
        try:
            self.log("Connecting ADB...")
            
            # ADB connect command
            result = subprocess.run(
                ['adb', 'connect', self.device],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'connected' in result.stdout.lower():
                self.adb_connected = True
                self.log("ADB connected successfully")
                return True
            else:
                self.log(f"ADB connection failed: {result.stdout}", 'error')
                return False
                
        except Exception as e:
            self.log(f"ADB connection error: {e}", 'error')
            return False
    
    def take_screenshot(self):
        """Take screenshot from device"""
        try:
            # Screenshot to device
            subprocess.run(['adb', '-s', self.device, 'shell', 'screencap', '-p', '/sdcard/screen.png'], check=True)
            
            # Pull to local (unique filename per user)
            screenshot_path = f'/tmp/screen_{self.user_id}.png'
            subprocess.run(['adb', '-s', self.device, 'pull', '/sdcard/screen.png', screenshot_path], check=True)
            
            # Load with OpenCV
            img = cv2.imread(screenshot_path)
            return img
            
        except Exception as e:
            self.log(f"Screenshot error: {e}", 'error')
            return None
    
    def find_truck_icon(self, screenshot):
        """Find truck icon using template matching"""
        try:
            # Load template
            template = cv2.imread(self.template_path)
            if template is None:
                self.log("Template image not found!", 'error')
                return None
            
            # Template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Threshold (lowered for testing)
            threshold = 0.50
            if max_val >= threshold:
                # Get center coordinates
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                self.log(f"Truck found", 'success')
                return (center_x, center_y)
            else:
                return None  # No log needed, happens often
                
        except Exception as e:
            self.log(f"Error finding truck: {e}", 'error')
            return None
    
    def tap(self, x, y):
        """Execute tap on device"""
        try:
            subprocess.run(['adb', '-s', self.device, 'shell', 'input', 'tap', str(x), str(y)], check=True)
            time.sleep(0.5)  # Wait for UI reaction
            return True
        except Exception as e:
            self.log(f"Tap error at ({x},{y}): {e}", 'error')
            return False
    
    def read_truck_info(self):
        """Read truck information using OCR"""
        try:
            # Take screenshot
            screenshot = self.take_screenshot()
            if screenshot is None:
                return {}
            
            info = {}
            
            # Read strength
            strength_region = self.OCR_REGIONS['strength']
            strength_img = screenshot[strength_region[1]:strength_region[3], strength_region[0]:strength_region[2]]
            strength_text = pytesseract.image_to_string(strength_img, config='--psm 7')
            
            # Extract number (e.g., "65.5M" -> 65.5)
            strength_match = re.search(r'([\d.]+)', strength_text)
            if strength_match:
                info['strength'] = float(strength_match.group(1))
            
            # Read server
            server_region = self.OCR_REGIONS['server']
            server_img = screenshot[server_region[1]:server_region[3], server_region[0]:server_region[2]]
            server_text = pytesseract.image_to_string(server_img, config='--psm 7')
            
            # Extract number (e.g., "#49" -> 49)
            server_match = re.search(r'#?(\d+)', server_text)
            if server_match:
                info['server'] = int(server_match.group(1))
            
            return info
            
        except Exception as e:
            self.log(f"OCR error: {e}", 'error')
            return {}
    
    def validate_truck(self, truck_info):
        """Validate if truck meets user's criteria"""
        # Check strength limit
        if 'strength' in truck_info:
            if truck_info['strength'] > self.config.truck_strength:
                self.log(f"Truck too strong ({truck_info['strength']}M), skipping", 'info')
                return False
        
        # Check server restriction
        if self.config.server_restriction_enabled and 'server' in truck_info:
            if truck_info['server'] != self.config.server_restriction_value:
                self.log(f"Wrong server (#{truck_info['server']}), skipping", 'info')
                return False
        
        return True
    
    def share_truck(self, truck_coords):
        """Share truck in chat"""
        try:
            self.log(f"Checking truck...")
            
            # 1. Click on truck icon
            if not self.tap(truck_coords[0], truck_coords[1]):
                return False
            
            time.sleep(1.5)
            
            # 2. Read truck info
            truck_info = self.read_truck_info()
            
            # 3. Validate truck
            if not self.validate_truck(truck_info):
                self.tap(self.COORDS['refresh'][0], self.COORDS['refresh'][1])
                return False
            
            # 4. Share button
            if not self.tap(self.COORDS['share'][0], self.COORDS['share'][1]):
                return False
            
            time.sleep(1)
            
            # 5. Share in chat
            if self.config.share_alliance:
                self.tap(self.COORDS['share_alliance_channel'][0], self.COORDS['share_alliance_channel'][1])
                time.sleep(0.5)
                self.tap(self.COORDS['share_alliance_confirm'][0], self.COORDS['share_alliance_confirm'][1])
                self.log(f"Shared in Alliance", 'success')
            elif self.config.share_world:
                self.tap(self.COORDS['share_world_channel'][0], self.COORDS['share_world_channel'][1])
                time.sleep(0.5)
                self.tap(self.COORDS['share_world_confirm'][0], self.COORDS['share_world_confirm'][1])
                self.log(f"Shared in World", 'success')
            
            time.sleep(1)
            
            # 6. Refresh
            self.tap(self.COORDS['refresh'][0], self.COORDS['refresh'][1])
            time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log(f"Error sharing: {e}", 'error')
            return False
    
    def run_cycle(self):
        """Run one bot cycle"""
        try:
            # Take screenshot
            screenshot = self.take_screenshot()
            if screenshot is None:
                return False
            
            # Find truck icon
            truck_coords = self.find_truck_icon(screenshot)
            if truck_coords is None:
                # Click refresh to search for new trucks
                self.tap(self.COORDS['refresh'][0], self.COORDS['refresh'][1])
                return True  # No truck found is not an error
            
            # Share truck
            if self.share_truck(truck_coords):
                # Remember this truck (simple coord-based for now)
                self.shared_trucks.add(truck_coords)
                return True
            
            return False
            
        except Exception as e:
            self.log(f"Cycle error: {e}", 'error')
            return False
    
    def run(self):
        """Main bot loop"""
        try:
            self.log("Starting main bot loop...")
            
            while True:
                # Check if bot should stop (DB query in each cycle)
                timer = BotTimer.query.filter_by(user_id=self.user_id, stopped_at=None).first()
                if not timer:
                    self.log("Bot stop signal received, exiting loop")
                    break
                
                self.run_cycle()
                time.sleep(3)
                
        except KeyboardInterrupt:
            self.log("Bot stopped by user")
        except Exception as e:
            self.log(f"Bot error: {e}", 'error')
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.log("Cleaning up...")
            
            # Disconnect ADB
            if self.adb_connected:
                subprocess.run(['adb', 'disconnect', self.device])
            
            # Kill SSH tunnel
            if self.ssh_tunnel_process:
                self.ssh_tunnel_process.terminate()
            
            # Also kill any lingering SSH processes for this port
            subprocess.run(['pkill', '-f', f'{self.config.local_adb_port}:adb-proxy'])
            
            self.log("Cleanup complete")
            
        except Exception as e:
            self.log(f"Cleanup error: {e}", 'error')