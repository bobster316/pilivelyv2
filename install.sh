#!/bin/bash
# Lively Pi - Installation Script for Raspberry Pi OS 64-bit

set -e

echo "🎨 Lively Pi Installation Script"
echo "Installing animated wallpaper manager for Raspberry Pi OS..."

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    echo "✅ Detected: $(cat /proc/device-tree/model)"
else
    echo "⚠️  This script is optimized for Raspberry Pi OS"
    echo "Continuing with installation..."
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6.qtmultimedia
sudo apt install -y mpv libmpv-dev vlc feh xrandr wmctrl xwininfo pulseaudio-utils git

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install --user PyQt6 python-mpv python-vlc psutil requests

# Create installation directory
INSTALL_DIR="$HOME/.local/share/lively-pi"
echo "📁 Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy application files
echo "📋 Installing Lively Pi application..."
cp src/lively_pi.py "$INSTALL_DIR/"
cp -r samples "$INSTALL_DIR/" 2>/dev/null || echo "No samples directory found"
chmod +x "$INSTALL_DIR/lively_pi.py"

# Create command line symlink
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/lively-pi" << 'EOF'
#!/bin/bash
exec python3 "$HOME/.local/share/lively-pi/lively_pi.py" "$@"
EOF
chmod +x "$BIN_DIR/lively-pi"

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "📝 Added ~/.local/bin to PATH in .bashrc"
fi

# Create desktop entry
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/lively-pi.desktop" << 'EOF'
[Desktop Entry]
Name=Lively Pi
Comment=Animated Wallpaper Manager for Raspberry Pi
Exec=/home/pi/.local/bin/lively-pi
Terminal=false
Type=Application
Categories=Graphics;Utility;
StartupNotify=true
EOF

echo ""
echo "✅ Lively Pi installed successfully!"
echo ""
echo "🚀 To start Lively Pi:"
echo "  • Run 'lively-pi' from terminal"
echo "  • Or find 'Lively Pi' in applications menu"
echo "  • Or restart terminal and run 'lively-pi'"
echo ""
echo "📁 Sample wallpapers installed in:"
echo "  $INSTALL_DIR/samples/"
echo ""
echo "🎉 Enjoy your animated wallpapers on Raspberry Pi!"
