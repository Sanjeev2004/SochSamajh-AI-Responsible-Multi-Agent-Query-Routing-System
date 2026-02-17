#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "Build completed successfully!"

