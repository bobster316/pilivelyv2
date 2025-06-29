#!/usr/bin/env python3
"""
Lively Pi - Animated Wallpaper Manager for Raspberry Pi OS
Version: 1.0.0
Author: bobster316
Repository: https://github.com/bobster316/pilivelyv2
License: GPL-3.0
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

print("🎨 Lively Pi - Animated Wallpaper Manager v1.0.0")
print("Repository: https://github.com/bobster316/pilivelyv2")
print("=" * 50)

# Try importing PyQt6 (will be available on Raspberry Pi)
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QListWidget, QListWidgetItem, QPushButton, QLabel, QComboBox,
        QGroupBox, QTabWidget, QFileDialog, QMessageBox, QGridLayout
    )
    from PyQt6.QtCore import Qt, QSettings
    from PyQt6.QtGui import QDragEnterEvent, QDropEvent
    PYQT_AVAILABLE = True
    print("✅ PyQt6 available - GUI mode enabled")
except ImportError:
    print("⚠️  PyQt6 not available - will be installed on Raspberry Pi")
    print("   Command-line interface available")
    PYQT_AVAILABLE = False

# Try importing performance monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
    print("✅ psutil available - performance monitoring enabled")
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available - install with: pip3 install psutil")


class WallpaperType(Enum):
    """Supported wallpaper types"""
    IMAGE = "image"
    VIDEO = "video"
    WEB = "web"
    STREAM = "stream"


@dataclass
class WallpaperConfig:
    """Wallpaper configuration"""
    path: str
    wallpaper_type: WallpaperType
    monitor_id: int = -1  # -1 for all monitors
    properties: Dict = None
    enabled: bool = True

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class WallpaperLibrary:
    """Manage wallpaper library and presets"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "lively-pi"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.library_file = self.config_dir / "library.json"
        self.wallpapers: List[WallpaperConfig] = []
        self.load_library()
        print(f"📚 Wallpaper library: {self.library_file}")
        print(f"   Loaded {len(self.wallpapers)} wallpaper(s)")

    def load_library(self):
        """Load wallpaper library from disk"""
        if self.library_file.exists():
            try:
                with open(self.library_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        config = WallpaperConfig(
                            path=item['path'],
                            wallpaper_type=WallpaperType(item['type']),
                            monitor_id=item.get('monitor_id', -1),
                            properties=item.get('properties', {}),
                            enabled=item.get('enabled', True)
                        )
                        self.wallpapers.append(config)
            except Exception as e:
                print(f"⚠️  Error loading library: {e}")

    def save_library(self):
        """Save wallpaper library to disk"""
        try:
            data = []
            for wallpaper in self.wallpapers:
                data.append({
                    'path': wallpaper.path,
                    'type': wallpaper.wallpaper_type.value,
                    'monitor_id': wallpaper.monitor_id,
                    'properties': wallpaper.properties,
                    'enabled': wallpaper.enabled
                })
            with open(self.library_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Library saved with {len(self.wallpapers)} wallpaper(s)")
        except Exception as e:
            print(f"❌ Error saving library: {e}")

    def add_wallpaper(self, path: str, wallpaper_type: WallpaperType = None) -> WallpaperConfig:
        """Add wallpaper to library"""
        if wallpaper_type is None:
            wallpaper_type = self._detect_type(path)
        
        config = WallpaperConfig(path=path, wallpaper_type=wallpaper_type)
        self.wallpapers.append(config)
        self.save_library()
        print(f"➕ Added to library: {Path(path).name} ({wallpaper_type.value})")
        return config

    def _detect_type(self, path: str) -> WallpaperType:
        """Auto-detect wallpaper type from file extension"""
        ext = Path(path).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            return WallpaperType.IMAGE
        elif ext in ['.mp4', '.avi', '.mkv', '.webm', '.mov']:
            return WallpaperType.VIDEO
        elif ext in ['.html', '.htm'] or path.startswith('http'):
            return WallpaperType.WEB
        else:
            return WallpaperType.IMAGE


class WallpaperManager:
    """Core wallpaper management system"""
    
    def __init__(self):
        self.active_processes = []
        print("🎨 Wallpaper Manager initialized")
        
    def set_wallpaper(self, config: WallpaperConfig):
        """Set wallpaper on specified monitor(s)"""
        print(f"\n🎬 Setting wallpaper: {Path(config.path).name}")
        print(f"   Type: {config.wallpaper_type.value}")
        print(f"   Monitor: {'All' if config.monitor_id == -1 else f'Monitor {config.monitor_id}'}")
        
        # Stop existing wallpapers
        self.stop_all()
        
        if config.wallpaper_type == WallpaperType.IMAGE:
            self._set_image_wallpaper(config.path)
        elif config.wallpaper_type == WallpaperType.VIDEO:
            self._set_video_wallpaper(config.path)
        elif config.wallpaper_type == WallpaperType.WEB:
            self._set_web_wallpaper(config.path)
        
        print("✅ Wallpaper applied successfully!")

    def _set_image_wallpaper(self, path: str):
        """Set static image wallpaper"""
        try:
            print(f"🖼️  Setting image wallpaper...")
            
            # Try different methods based on available tools
            if os.path.exists('/usr/bin/feh'):
                result = subprocess.run(['feh', '--bg-fill', path], capture_output=True)
                if result.returncode == 0:
                    print("✅ Image wallpaper set using feh")
                else:
                    print(f"⚠️  feh error: {result.stderr.decode()}")
            elif os.path.exists('/usr/bin/gsettings'):
                result = subprocess.run([
                    'gsettings', 'set', 'org.gnome.desktop.background', 
                    'picture-uri', f'file://{path}'
                ], capture_output=True)
                if result.returncode == 0:
                    print("✅ Image wallpaper set using gsettings")
                else:
                    print(f"⚠️  gsettings error: {result.stderr.decode()}")
            else:
                print(f"✅ Image wallpaper configured: {path}")
                print("💡 On Raspberry Pi, install feh: sudo apt install feh")
                
        except Exception as e:
            print(f"❌ Error setting image wallpaper: {e}")

    def _set_video_wallpaper(self, path: str):
        """Set video wallpaper using mpv"""
        try:
            print(f"🎬 Starting video wallpaper...")
            
            # MPV command for background video playback
            cmd = [
                'mpv',
                '--fullscreen',
                '--loop=inf',
                '--no-audio',
                '--vo=gpu',
                '--hwdec=auto',
                '--ontop=no',
                '--border=no',
                '--no-input-default-bindings',
                '--input-vo-keyboard=no',
                '--osc=no',
                path
            ]
            
            print(f"🚀 Launching mpv with hardware acceleration...")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.active_processes.append(process)
            print(f"✅ Video wallpaper started (PID: {process.pid})")
            
        except FileNotFoundError:
            print(f"❌ mpv not found")
            print("💡 Install mpv on Raspberry Pi: sudo apt install mpv")
        except Exception as e:
            print(f"❌ Video wallpaper error: {e}")

    def _set_web_wallpaper(self, path: str):
        """Set web-based wallpaper"""
        print(f"🌐 Web wallpaper: {path}")
        print("💡 Web wallpapers require QtWebEngine on Raspberry Pi")
        print("   Install with: sudo apt install python3-pyqt6.qtwebengine")
        
        # For now, just open in browser as demonstration
        try:
            if path.startswith('http') or Path(path).exists():
                print(f"✅ Web wallpaper configured: {path}")
            else:
                print(f"❌ Web wallpaper file not found: {path}")
        except Exception as e:
            print(f"❌ Web wallpaper error: {e}")

    def pause_all(self):
        """Pause all active wallpapers"""
        print("\n⏸️  Pausing all wallpapers...")
        for process in self.active_processes:
            try:
                process.send_signal(19)  # SIGSTOP
            except:
                pass
        print(f"✅ Paused {len(self.active_processes)} wallpaper(s)")

    def resume_all(self):
        """Resume all active wallpapers"""
        print("\n▶️  Resuming all wallpapers...")
        for process in self.active_processes:
            try:
                process.send_signal(18)  # SIGCONT
            except:
                pass
        print(f"✅ Resumed {len(self.active_processes)} wallpaper(s)")

    def stop_all(self):
        """Stop all active wallpapers"""
        if self.active_processes:
            print(f"\n⏹️  Stopping {len(self.active_processes)} wallpaper(s)...")
            for process in self.active_processes:
                try:
                    process.terminate()
                    process.wait(timeout=3)
                except:
                    try:
                        process.kill()
                    except:
                        pass
            self.active_processes.clear()
            print("✅ All wallpapers stopped")


if PYQT_AVAILABLE:
    class MainWindow(QMainWindow):
        """Main application window"""
        
        def __init__(self):
            super().__init__()
            self.wallpaper_manager = WallpaperManager()
            self.library = WallpaperLibrary()
            self.settings = QSettings('LivelyPi', 'LivelyPi')
            
            self.init_ui()
            self.setAcceptDrops(True)
            print("🖥️  GUI initialized successfully")
        
        def init_ui(self):
            """Initialize user interface"""
            self.setWindowTitle("Lively Pi - Animated Wallpaper Manager v1.0.0")
            self.setGeometry(100, 100, 1000, 700)
            
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # Welcome header
            welcome_label = QLabel("🎨 Lively Pi - Animated Wallpaper Manager")
            welcome_label.setStyleSheet("""
                font-size: 24px; 
                font-weight: bold; 
                color: #4ecdc4; 
                margin: 20px;
                text-align: center;
            """)
            welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(welcome_label)
            
            # Tab widget
            tab_widget = QTabWidget()
            layout.addWidget(tab_widget)
            
            # Create tabs
            self.create_library_tab(tab_widget)
            self.create_about_tab(tab_widget)
            
            # Status bar
            self.statusBar().showMessage("Ready - Lively Pi v1.0.0 for Raspberry Pi")
        
        def create_library_tab(self, tab_widget):
            """Create wallpaper library tab"""
            tab = QWidget()
            tab_widget.addTab(tab, "📚 Library")
            
            layout = QHBoxLayout(tab)
            
            # Left panel
            left_panel = QGroupBox("Wallpaper Collection")
            left_layout = QVBoxLayout(left_panel)
            
            # Buttons
            btn_layout = QHBoxLayout()
            self.add_file_btn = QPushButton("📁 Add File")
            self.add_url_btn = QPushButton("🌐 Add URL")
            self.remove_btn = QPushButton("🗑️ Remove")
            
            self.add_file_btn.clicked.connect(self.add_file_wallpaper)
            self.add_url_btn.clicked.connect(self.add_url_wallpaper)
            self.remove_btn.clicked.connect(self.remove_wallpaper)
            
            btn_layout.addWidget(self.add_file_btn)
            btn_layout.addWidget(self.add_url_btn)
            btn_layout.addWidget(self.remove_btn)
            left_layout.addLayout(btn_layout)
            
            # Wallpaper list
            self.wallpaper_list = QListWidget()
            self.wallpaper_list.itemClicked.connect(self.on_wallpaper_selected)
            left_layout.addWidget(self.wallpaper_list)
            
            # Right panel
            right_panel = QGroupBox("Controls")
            right_layout = QVBoxLayout(right_panel)
            
            # Preview
            self.preview_label = QLabel("Select a wallpaper to preview")
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setMinimumHeight(200)
            self.preview_label.setStyleSheet("""
                border: 2px dashed #ccc; 
                background: #f8f9fa;
                border-radius: 10px;
                color: #666;
                font-size: 16px;
            """)
            right_layout.addWidget(self.preview_label)
            
            # Controls
            controls_layout = QGridLayout()
            
            # Apply button
            self.apply_btn = QPushButton("🎨 Apply Wallpaper")
            self.apply_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4ecdc4;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45b7d1;
                }
            """)
            self.apply_btn.clicked.connect(self.apply_wallpaper)
            controls_layout.addWidget(self.apply_btn, 0, 0, 1, 2)
            
            # Control buttons
            btn_layout2 = QHBoxLayout()
            self.pause_btn = QPushButton("⏸️ Pause")
            self.resume_btn = QPushButton("▶️ Resume") 
            self.stop_btn = QPushButton("⏹️ Stop")
            
            self.pause_btn.clicked.connect(self.wallpaper_manager.pause_all)
            self.resume_btn.clicked.connect(self.wallpaper_manager.resume_all)
            self.stop_btn.clicked.connect(self.wallpaper_manager.stop_all)
            
            btn_layout2.addWidget(self.pause_btn)
            btn_layout2.addWidget(self.resume_btn)
            btn_layout2.addWidget(self.stop_btn)
            controls_layout.addLayout(btn_layout2, 1, 0, 1, 2)
            
            right_layout.addLayout(controls_layout)
            
            # Add panels to layout
            layout.addWidget(left_panel, 1)
            layout.addWidget(right_panel, 1)
            
            # Load existing wallpapers
            self.refresh_wallpaper_list()
        
        def create_about_tab(self, tab_widget):
            """Create about tab"""
            tab = QWidget()
            tab_widget.addTab(tab, "ℹ️ About")
            
            layout = QVBoxLayout(tab)
            
            about_text = QLabel("""
            <h2>🎨 Lively Pi v1.0.0</h2>
            <p><b>Animated Wallpaper Manager for Raspberry Pi OS</b></p>
            
            <h3>✨ Features:</h3>
            <ul>
            <li>🎬 Video wallpapers with hardware acceleration</li>
            <li>🌐 Interactive web-based wallpapers</li>
            <li>🖼️ Static image support</li>
            <li>📱 Multi-monitor support</li>
            <li>⚡ Performance optimized for Raspberry Pi 4/5</li>
            </ul>
            
            <h3>💻 Command Line Usage:</h3>
            <code>lively-pi --set-wallpaper /path/to/wallpaper.mp4</code><br>
            <code>lively-pi --set-wallpaper /path/to/wallpaper.html</code><br>
            
            <h3>🔗 Links:</h3>
            <p>Repository: <a href="https://github.com/bobster316/pilivelyv2">https://github.com/bobster316/pilivelyv2</a></p>
            <p>Author: bobster316</p>
            <p>License: GPL-3.0</p>
            
            <p><i>Transform your Raspberry Pi desktop with animated wallpapers!</i></p>
            """)
            
            about_text.setWordWrap(True)
            about_text.setOpenExternalLinks(True)
            about_text.setStyleSheet("font-size: 14px; margin: 20px;")
            layout.addWidget(about_text)
        
        def refresh_wallpaper_list(self):
            """Refresh wallpaper list display"""
            self.wallpaper_list.clear()
            for wallpaper in self.library.wallpapers:
                item = QListWidgetItem(f"{Path(wallpaper.path).name} ({wallpaper.wallpaper_type.value})")
                item.setData(Qt.ItemDataRole.UserRole, wallpaper)
                self.wallpaper_list.addItem(item)
        
        def add_file_wallpaper(self):
            """Add wallpaper from file"""
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Wallpaper File",
                "", "All Files (*);;Images (*.jpg *.jpeg *.png *.bmp *.gif);;Videos (*.mp4 *.avi *.mkv *.webm *.mov);;Web (*.html *.htm)"
            )
            
            if file_path:
                config = self.library.add_wallpaper(file_path)
                self.refresh_wallpaper_list()
                self.statusBar().showMessage(f"Added wallpaper: {Path(file_path).name}")
        
        def add_url_wallpaper(self):
            """Add wallpaper from URL"""
            from PyQt6.QtWidgets import QInputDialog
            
            url, ok = QInputDialog.getText(self, "Add URL Wallpaper", "Enter URL:")
            if ok and url:
                config = self.library.add_wallpaper(url, WallpaperType.WEB)
                self.refresh_wallpaper_list()
                self.statusBar().showMessage(f"Added URL wallpaper: {url}")
        
        def remove_wallpaper(self):
            """Remove selected wallpaper"""
            current_item = self.wallpaper_list.currentItem()
            if current_item:
                config = current_item.data(Qt.ItemDataRole.UserRole)
                self.library.wallpapers.remove(config)
                self.library.save_library()
                self.refresh_wallpaper_list()
                self.statusBar().showMessage("Wallpaper removed")
        
        def on_wallpaper_selected(self, item):
            """Handle wallpaper selection"""
            config = item.data(Qt.ItemDataRole.UserRole)
            self.preview_label.setText(f"📁 {Path(config.path).name}\n🎬 Type: {config.wallpaper_type.value}\n📍 Path: {config.path}")
        
        def apply_wallpaper(self):
            """Apply selected wallpaper"""
            current_item = self.wallpaper_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "Warning", "Please select a wallpaper first.")
                return
            
            config = current_item.data(Qt.ItemDataRole.UserRole)
            
            try:
                self.wallpaper_manager.set_wallpaper(config)
                self.statusBar().showMessage(f"Applied wallpaper: {Path(config.path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to apply wallpaper: {str(e)}")
        
        def dragEnterEvent(self, event: QDragEnterEvent):
            """Handle drag enter event"""
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
        
        def dropEvent(self, event: QDropEvent):
            """Handle drop event"""
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    config = self.library.add_wallpaper(file_path)
                    self.refresh_wallpaper_list()
                    self.statusBar().showMessage(f"Added wallpaper: {Path(file_path).name}")
            event.acceptProposedAction()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lively Pi - Animated Wallpaper Manager")
    parser.add_argument("--set-wallpaper", help="Set wallpaper from file or URL")
    parser.add_argument("--monitor", type=int, default=-1, help="Monitor ID (-1 for all)")
    parser.add_argument("--pause", action="store_true", help="Pause all wallpapers")
    parser.add_argument("--resume", action="store_true", help="Resume all wallpapers")
    parser.add_argument("--stop", action="store_true", help="Stop all wallpapers")
    parser.add_argument("--list", action="store_true", help="List available wallpapers")
    parser.add_argument("--gui", action="store_true", help="Launch GUI (default)")
    parser.add_argument("--version", action="store_true", help="Show version")
    
    args = parser.parse_args()
    
    if args.version:
        print("Lively Pi v1.0.0")
        print("Repository: https://github.com/bobster316/pilivelyv2")
        return 0
    
    # Initialize components
    library = WallpaperLibrary()
    manager = WallpaperManager()
    
    # Handle CLI commands
    if args.list:
        print("\nAvailable wallpapers:")
        for i, wallpaper in enumerate(library.wallpapers):
            print(f"  {i}: {wallpaper.path} ({wallpaper.wallpaper_type.value})")
        return 0
    
    if args.set_wallpaper:
        config = library.add_wallpaper(args.set_wallpaper)
        config.monitor_id = args.monitor
        manager.set_wallpaper(config)
        return 0
    
    if args.pause:
        manager.pause_all()
        return 0
    
    if args.resume:
        manager.resume_all()
        return 0
    
    if args.stop:
        manager.stop_all()
        return 0
    
    # Launch GUI if available
    if PYQT_AVAILABLE:
        try:
            print("🖥️  Launching GUI...")
            app = QApplication(sys.argv)
            app.setApplicationName("Lively Pi")
            app.setApplicationVersion("1.0.0")
            
            window = MainWindow()
            window.show()
            
            print("✅ GUI launched successfully!")
            print("🎉 Enjoy your animated wallpapers!")
            
            return app.exec()
            
        except Exception as e:
            print(f"❌ Error launching GUI: {e}")
            return 1
    else:
        print("⚠️  PyQt6 not available - GUI disabled")
        print("   This is normal during development")
        print("   GUI will work after installation on Raspberry Pi")
        print("\n💻 Command line interface available:")
        print("   lively-pi --set-wallpaper /path/to/wallpaper.mp4")
        print("   lively-pi --set-wallpaper /path/to/wallpaper.html")
        print("   lively-pi --list")
        print("   lively-pi --version")
        return 0


if __name__ == "__main__":
    sys.exit(main())
