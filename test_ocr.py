#!/usr/bin/env python3
"""
Simple test script to verify OCR functionality.
"""
import sys
import subprocess
import tempfile
from ocr_engine import OCREngine

def test_screenshot_and_ocr():
    """Test screenshot capture and OCR."""
    print("=== Testing Screenshot & OCR ===\n")
    
    # Capture screenshot with spectacle
    print("1. Capturing screenshot with spectacle...")
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    result = subprocess.run(
        ['spectacle', '-b', '-n', '-o', temp_path],
        capture_output=True,
        timeout=5
    )
    
    if result.returncode != 0:
        print(f"   ✗ Screenshot failed: {result.stderr.decode()}")
        return False
    
    print(f"   ✓ Screenshot saved: {temp_path}")
    
    # Initialize OCR engine
    print("\n2. Initializing OCR engine...")
    ocr = OCREngine()
    print("   ✓ OCR engine ready")
    
    # Ask user for region
    print("\n3. Enter region to extract text from:")
    print("   Format: x y width height (e.g., 100 100 400 200)")
    print("   Or press Enter to use full screenshot")
    
    region_input = input("   Region: ").strip()
    
    if region_input:
        try:
            x, y, w, h = map(int, region_input.split())
            region = (x, y, w, h)
        except ValueError:
            print("   Invalid input, using full screenshot")
            # Get image dimensions
            import cv2
            img = cv2.imread(temp_path)
            h, w = img.shape[:2]
            region = (0, 0, w, h)
    else:
        # Get image dimensions for full screenshot
        import cv2
        img = cv2.imread(temp_path)
        h, w = img.shape[:2]
        region = (0, 0, w, h)
        print(f"   Using full screenshot: {region}")
    
    # Run OCR
    print("\n4. Running OCR...")
    text = ocr.extract_text(temp_path, region)
    
    print(f"\n5. Results:")
    print(f"   Length: {len(text)} characters")
    print(f"   Text: '{text}'")
    
    if text.strip():
        print("\n   ✓ OCR successful!")
        # Copy to clipboard
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QGuiApplication
            
            app = QApplication.instance() or QApplication(sys.argv)
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            print("   ✓ Copied to clipboard")
        except Exception as e:
            print(f"   ⚠ Could not copy to clipboard: {e}")
        
        return True
    else:
        print("\n   ⚠ No text extracted")
        return False

if __name__ == '__main__':
    try:
        success = test_screenshot_and_ocr()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
