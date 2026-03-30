#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ADDIN_DIR="$PROJECT_DIR/powerpoint-addin"

cd "$ADDIN_DIR"

# Install node deps if missing
if [ ! -d "node_modules" ]; then
  echo "Installing Node.js dependencies..."
  npm install
fi

# Install HTTPS dev certs
echo "Installing dev HTTPS certificates (may ask for your password)..."
npx office-addin-dev-certs install || echo "Certs may already be installed."

# Sideload manifest to PowerPoint on Mac
MANIFEST_SRC="$ADDIN_DIR/manifest.xml"
WEF_DIR="$HOME/Library/Containers/com.microsoft.Powerpoint/Data/Documents/wef"
mkdir -p "$WEF_DIR"
cp "$MANIFEST_SRC" "$WEF_DIR/PresentationCoach.xml"
echo "Manifest sideloaded to: $WEF_DIR"

echo ""
echo "Starting webpack dev server on https://localhost:3000"
echo "Open PowerPoint -> Insert -> My Add-ins -> Presentation Coach"
echo ""

npm run dev
