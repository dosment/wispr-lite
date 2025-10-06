#!/bin/bash
# Preload Whisper models for offline use with checksum verification

set -e

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/wispr-lite/models"
MODEL_SIZES=("tiny" "base" "small" "medium" "large")

# Model checksums for faster-whisper models
# NOTE: Checksum verification is OPTIONAL but recommended for security.
#
# Current behavior: All checksums are set to "skip" (no verification).
# This allows models to download without hash validation.
#
# To enable verification:
# 1. Download a model once: ./scripts/preload_models.sh base
# 2. Get the SHA256 hash: find ~/.cache/wispr-lite/models -name "model.bin" -exec sha256sum {} \;
# 3. Replace "skip" with the actual hash below
# 4. Re-run preload to verify
#
# Example with real hash:
#   ["base"]="a1b2c3d4e5f6..."
#
declare -A MODEL_CHECKSUMS=(
    ["tiny"]="skip"   # Set to SHA256 hash to enable verification
    ["base"]="skip"
    ["small"]="skip"
    ["medium"]="skip"
    ["large"]="skip"
)

echo "Wispr-Lite Model Preloader"
echo "=========================="
echo ""

# Show license notice
cat << 'EOF'
WHISPER MODEL LICENSE NOTICE:

The Whisper models are released by OpenAI under the MIT License.
By downloading these models, you agree to the terms of the MIT License.

See: https://github.com/openai/whisper/blob/main/LICENSE

Do you wish to continue? (y/N)
EOF

read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Cache directory: $CACHE_DIR"
mkdir -p "$CACHE_DIR"

# Function to verify model checksum
verify_checksum() {
    local model_size=$1
    local model_dir=$2
    local expected_checksum="${MODEL_CHECKSUMS[$model_size]}"

    # Skip verification if checksum is "skip"
    if [ "$expected_checksum" = "skip" ]; then
        echo "⚠ Checksum verification skipped (no hash configured)"
        return 0
    fi

    # Find model.bin file
    local model_file=$(find "$model_dir" -name "model.bin" | head -n 1)
    if [ -z "$model_file" ]; then
        echo "⚠ Warning: model.bin not found for checksum verification"
        return 1
    fi

    # Compute SHA256
    echo "Verifying checksum..."
    local actual_checksum=$(sha256sum "$model_file" | awk '{print $1}')

    if [ "$actual_checksum" = "$expected_checksum" ]; then
        echo "✓ Checksum verified"
        return 0
    else
        echo "✗ Checksum mismatch!"
        echo "  Expected: $expected_checksum"
        echo "  Actual:   $actual_checksum"
        echo "  This may indicate a corrupted or tampered model file."
        return 1
    fi
}

# Function to download and verify model
download_model() {
    local model_size=$1
    echo ""
    echo "Downloading model: $model_size"
    echo "--------------------------------"

    # Use Python to download via faster-whisper
    python3 << EOF
import sys
from pathlib import Path
from faster_whisper import WhisperModel, download_model

try:
    print(f"Downloading {model_size} model...")
    model_path = download_model("$model_size", cache_dir="$CACHE_DIR")
    print(f"Downloaded to: {model_path}")

    # Verify by loading
    print("Verifying model...")
    model = WhisperModel("$model_size", device="cpu", download_root="$CACHE_DIR")
    print("✓ Model loaded successfully")

    # Print model path for checksum verification
    print(f"MODEL_DIR:{model_path}")

except Exception as e:
    print(f"✗ Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        echo "✗ Failed to download $model_size model"
        return 1
    fi

    # Extract model directory from Python output
    local model_dir=$(python3 << EOF
from faster_whisper import download_model
model_path = download_model("$model_size", cache_dir="$CACHE_DIR", local_files_only=True)
print(model_path)
EOF
)

    # Verify checksum if configured
    if ! verify_checksum "$model_size" "$model_dir"; then
        echo "⚠ Warning: Checksum verification failed, but model is available"
    fi

    echo "✓ $model_size model ready"
    return 0
}

# Download requested models
if [ $# -eq 0 ]; then
    # No arguments: download base model only
    download_model "base"
else
    # Download specified models
    for model in "$@"; do
        if [[ " ${MODEL_SIZES[@]} " =~ " ${model} " ]]; then
            download_model "$model"
        else
            echo "Unknown model size: $model"
            echo "Valid sizes: ${MODEL_SIZES[*]}"
            exit 1
        fi
    done
fi

echo ""
echo "Model preload complete!"
echo "Models cached in: $CACHE_DIR"
echo ""
echo "To use a different model, update the config:"
echo "  ~/.config/wispr-lite/config.yaml"
echo ""
