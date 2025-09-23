#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-download EasyOCR and PaddleOCR models script
Ensure model files are downloaded before packaging
"""

import os
import sys
from pathlib import Path

def download_easyocr_models():
    """Download required EasyOCR models"""
    print("Starting EasyOCR model download...")
    
    try:
        import easyocr
        
        # Initialize EasyOCR to download models
        print("Initializing EasyOCR with Chinese and English support...")
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, download_enabled=True, verbose=False)
        print("✅ EasyOCR models downloaded successfully")
        
        # Check model files
        home_dir = Path.home()
        easyocr_model_dir = home_dir / ".EasyOCR" / "model"
        
        if easyocr_model_dir.exists():
            model_files = list(easyocr_model_dir.glob("*.pth"))
            print(f"Found {len(model_files)} EasyOCR model files:")
            
            total_size = 0
            for model_file in model_files:
                size = model_file.stat().st_size / (1024 * 1024)
                total_size += size
                print(f"  - {model_file.name}: {size:.1f} MB")
            
            print(f"Total EasyOCR model size: {total_size:.1f} MB")
            print(f"Model storage path: {easyocr_model_dir}")
            return True
        else:
            print("❌ EasyOCR model directory not found")
            return False
            
    except ImportError:
        print("❌ EasyOCR not installed. Please run: pip install easyocr")
        return False
    except Exception as e:
        print(f"❌ EasyOCR model download failed: {e}")
        return False

def download_paddle_models():
    """Download PaddleOCR models as fallback"""
    print("\nStarting PaddleOCR model download (fallback)...")
    
    try:
        from paddleocr import PaddleOCR
        
        # Initialize PaddleOCR
        ocr = PaddleOCR(
            use_angle_cls=False,
            lang='ch'
        )
        print("✅ PaddleOCR models downloaded successfully")
        
        # Check model files
        paddlex_home = Path.home() / ".paddlex"
        if paddlex_home.exists():
            model_count = 0
            total_size = 0
            
            for root, dirs, files in os.walk(paddlex_home):
                for file in files:
                    if file.endswith(('.pdiparams', '.pdmodel', '.pth')):
                        model_count += 1
                        filepath = Path(root) / file
                        total_size += filepath.stat().st_size
            
            print(f"Found {model_count} PaddleOCR model files")
            print(f"Total PaddleOCR model size: {total_size / 1024 / 1024:.1f} MB")
            print(f"Model storage path: {paddlex_home}")
            return True
        else:
            print("⚠️  PaddleOCR model directory not found (optional)")
            return True  # Not critical since EasyOCR is primary
            
    except ImportError:
        print("⚠️  PaddleOCR not installed (optional)")
        return True  # Not critical
    except Exception as e:
        print(f"⚠️  PaddleOCR model download failed (optional): {e}")
        return True  # Not critical

def list_all_models():
    """List all OCR model files"""
    print("\n" + "=" * 60)
    print("OCR Model Summary")
    print("=" * 60)
    
    home_dir = Path.home()
    
    # EasyOCR models
    easyocr_dir = home_dir / ".EasyOCR" / "model"
    if easyocr_dir.exists():
        print("\nEasyOCR Models:")
        for model in easyocr_dir.glob("*.pth"):
            size = model.stat().st_size / (1024 * 1024)
            print(f"  ✓ {model.name}: {size:.1f} MB")
    else:
        print("\nEasyOCR Models: Not found")
    
    # PaddleOCR models
    paddlex_dir = home_dir / ".paddlex" / "official_models"
    if paddlex_dir.exists():
        print("\nPaddleOCR Models (fallback):")
        for model_dir in paddlex_dir.iterdir():
            if model_dir.is_dir():
                print(f"  ✓ {model_dir.name}")
    else:
        print("\nPaddleOCR Models: Not found (optional)")
    
    print("=" * 60)

def copy_models_for_packaging():
    """Copy model files to local directory for packaging"""
    print("\nCopying models for packaging...")
    
    import shutil
    
    # Create local model directories
    local_easyocr = Path("easyocr_models")
    local_paddle = Path("paddlex_models")
    
    local_easyocr.mkdir(exist_ok=True)
    
    # Copy EasyOCR models
    home_dir = Path.home()
    easyocr_source = home_dir / ".EasyOCR" / "model"
    
    if easyocr_source.exists():
        for model_file in easyocr_source.glob("*.pth"):
            dest = local_easyocr / model_file.name
            shutil.copy2(model_file, dest)
            print(f"  Copied: {model_file.name}")
    
    # Copy PaddleOCR models (optional)
    paddlex_source = home_dir / ".paddlex"
    if paddlex_source.exists():
        local_paddle.mkdir(exist_ok=True)
        if paddlex_source.exists():
            # Copy entire paddlex directory structure
            if local_paddle.exists():
                shutil.rmtree(local_paddle)
            shutil.copytree(paddlex_source, local_paddle)
            print(f"  Copied PaddleOCR models to {local_paddle}")
    
    print("✅ Model files copied for packaging")
    return True

if __name__ == "__main__":
    success = True
    
    # Download EasyOCR models (primary)
    if not download_easyocr_models():
        print("\n❌ EasyOCR model preparation failed (required)")
        success = False
    
    # Download PaddleOCR models (optional fallback)
    download_paddle_models()
    
    if success:
        # List all models
        list_all_models()
        
        # Copy models for packaging
        copy_models_for_packaging()
        
        print("\n✅ Model preparation completed, ready for packaging")
    else:
        print("\n❌ Model preparation failed")
        sys.exit(1)
