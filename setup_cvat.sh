#!/bin/bash
#
# Setup CVAT (Computer Vision Annotation Tool) via Docker
# For annotating your security footage to create training data
#

set -e

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              Setting Up CVAT Annotation Tool                         ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo ""
    echo "Please install Docker first:"
    echo "  macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "  Linux: https://docs.docker.com/engine/install/"
    echo ""
    exit 1
fi

echo "✅ Docker is installed: $(docker --version)"
echo ""

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available!"
    echo "Please install Docker Compose or upgrade Docker Desktop"
    exit 1
fi

echo "✅ Docker Compose is available"
echo ""

# Clone CVAT if not already present
if [ ! -d "cvat" ]; then
    echo "📥 Cloning CVAT repository..."
    git clone https://github.com/cvat-ai/cvat.git
    cd cvat
else
    echo "✅ CVAT repository already exists"
    cd cvat
    git pull origin develop
fi

echo ""
echo "🚀 Starting CVAT with Docker Compose..."
echo "════════════════════════════════════════════════════════════════════"
echo "This will download Docker images (~2-3 GB) on first run."
echo "It may take 5-10 minutes..."
echo ""

docker compose up -d

echo ""
echo "⏳ Waiting for CVAT to start..."
sleep 10

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║                    ✅ CVAT IS RUNNING!                                ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Access CVAT at: http://localhost:8080"
echo ""
echo "📋 First-time setup:"
echo "  1. Open http://localhost:8080 in your browser"
echo "  2. Click 'Create an account'"
echo "  3. Register with:"
echo "     Username: admin"
echo "     Email: admin@alibi.local"
echo "     Password: [choose a strong password]"
echo ""
echo "💡 Usage tips:"
echo "  • Upload your camera snapshots to create tasks"
echo "  • Annotate people, weapons, vehicles with bounding boxes"
echo "  • Export in COCO format for training"
echo "  • Use annotations to fine-tune Detectron2 models"
echo ""
echo "🛠️ Management commands:"
echo "  Stop CVAT:    docker compose down"
echo "  Start CVAT:   docker compose up -d"
echo "  View logs:    docker compose logs -f"
echo "  Restart:      docker compose restart"
echo ""
