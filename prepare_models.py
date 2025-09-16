#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-download PaddleOCR models script
Ensure model files are downloaded before packaging
"""

import os
import sys
from paddleocr import PaddleOCR

def download_models():
    """Download required PaddleOCR models"""
    print("Starting PaddleOCR model download...")
    
    try:
        # Initialize PaddleOCR, this will automatically download required models
        ocr = PaddleOCR(
            use_textline_orientation=True,
            lang='ch'
        )
        print("Chinese OCR models downloaded successfully")
        
        # Check if model files exist
        paddlex_home = os.path.expanduser("~/.paddlex")
        if os.path.exists(paddlex_home):
            model_count = 0
            for root, dirs, files in os.walk(paddlex_home):
                for file in files:
                    if file.endswith(('.pdiparams', '.pdmodel')):
                        model_count += 1
            print(f"Found {model_count} model files")
            print(f"Model storage path: {paddlex_home}")
        else:
            print("Model file directory not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"Model download failed: {e}")
        return False

def list_model_files():
    """List all model files"""
    paddlex_home = os.path.expanduser("~/.paddlex")
    if not os.path.exists(paddlex_home):
        print("Model directory does not exist")
        return
    
    print("\nModel file list:")
    print("=" * 50)
    
    total_size = 0
    for root, dirs, files in os.walk(paddlex_home):
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            total_size += size
            rel_path = os.path.relpath(filepath, paddlex_home)
            print(f"{rel_path} ({size / 1024 / 1024:.1f} MB)")
    
    print("=" * 50)
    print(f"Total size: {total_size / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    if download_models():
        list_model_files()
        print("\nModel preparation completed, ready for packaging")
    else:
        print("\nModel preparation failed")
        sys.exit(1)
