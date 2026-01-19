#!/bin/bash
#
# Install Computer Vision Tools for Alibi
# Installs: OpenCV, PyTorch, Detectron2
#

set -e

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║         Installing Advanced Computer Vision Tools for Alibi          ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Step 1: Installing PyTorch first (required for Detectron2)..."
echo "════════════════════════════════════════════════════════════════════"
pip install --upgrade pip
pip install 'torch>=2.1.0' 'torchvision>=0.16.0' 'torchaudio>=2.1.0'
echo "✅ PyTorch installed!"
echo ""

echo "📦 Step 2: Installing base requirements (OpenCV, etc.)..."
echo "════════════════════════════════════════════════════════════════════"
pip install 'opencv-python>=4.8.0' 'opencv-contrib-python>=4.8.0'
echo "✅ OpenCV installed!"
echo ""

echo "🚨 Step 3: Installing Detectron2 (optional - may not work on all systems)..."
echo "════════════════════════════════════════════════════════════════════"
echo "Note: Detectron2 installation can be tricky and may fail on macOS."
echo "      OpenCV provides good object detection without it."
echo ""

# Check if Detectron2 is already installed
if python3 -c "import detectron2" 2>/dev/null; then
    echo "✅ Detectron2 is already installed!"
else
    echo "Attempting to install Detectron2..."
    if pip install 'git+https://github.com/facebookresearch/detectron2.git' 2>/tmp/detectron2_install.log; then
        echo "✅ Detectron2 installed successfully!"
    else
        echo "⚠️  Detectron2 installation failed (this is normal on macOS)"
        echo "   You can still use OpenCV for object detection."
        echo "   Error log: /tmp/detectron2_install.log"
    fi
fi
echo ""

echo "🧪 Step 3: Verifying installations..."
echo "════════════════════════════════════════════════════════════════════"
python3 << 'EOF'
print("Testing OpenCV...")
import cv2
print(f"✅ OpenCV version: {cv2.__version__}")

print("\nTesting PyTorch...")
import torch
print(f"✅ PyTorch version: {torch.__version__}")
print(f"   CUDA available: {torch.cuda.is_available()}")
print(f"   CPU threads: {torch.get_num_threads()}")

print("\nTesting Detectron2...")
try:
    import detectron2
    from detectron2 import model_zoo
    print(f"✅ Detectron2 installed successfully!")
    print(f"   Available models: {len(model_zoo.get_available_models())} pretrained models")
except ImportError as e:
    print(f"❌ Detectron2 not available: {e}")
    print("   This is normal on some systems. You can use OpenCV detectors instead.")

print("\n✅ All core computer vision tools are ready!")
EOF

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║                  ✅ INSTALLATION COMPLETE!                            ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. For CVAT (annotation tool), run: ./setup_cvat.sh"
echo "  2. To test object detection, run: python3 test_detectron2.py"
echo "  3. Start Alibi: ./start_alibi.sh"
echo ""
