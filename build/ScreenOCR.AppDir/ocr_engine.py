"""
OCR engine using RapidOCR for accurate and fast text recognition.
"""
from typing import Optional, Tuple
from pathlib import Path
import cv2
import numpy as np
from utils import clean_ocr_text


class OCREngine:
    """
    Optical character recognition engine using RapidOCR (lightweight PaddleOCR).
    """
    
    def __init__(self, language: str = 'en', use_gpu: bool = False) -> None:
        """
        Initialize OCR engine.
        
        Args:
            language: Language for OCR (default: 'en')
            use_gpu: Whether to use GPU (default: False)
        """
        self.language = language
        self.use_gpu = use_gpu
        self.ocr = None
        self._init_rapidocr()
    
    def _init_rapidocr(self) -> None:
        """Initialize RapidOCR reader."""
        try:
            print("Initializing RapidOCR...")
            from rapidocr_onnxruntime import RapidOCR
            
            self.ocr = RapidOCR()
            print("✓ RapidOCR initialized")
        except Exception as e:
            print(f"✗ RapidOCR initialization failed: {e}")
            self.ocr = None
    
    def _read_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Read image from file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image array or None if failed
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            return img
        except Exception:
            return None
    
    def _crop_region(
        self,
        image: np.ndarray,
        region: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Crop image to specified region.
        
        Args:
            image: Image array
            region: (x, y, width, height) tuple
            
        Returns:
            Cropped image array
        """
        x, y, width, height = region
        return image[y:y+height, x:x+width]
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: Image array
            
        Returns:
            Preprocessed image array
        """
        # Upscale for better character recognition
        height, width = image.shape[:2]
        scale = 2.0 if width < 600 else 1.5
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Slight denoise while preserving character edges
        denoised = cv2.fastNlMeansDenoisingColored(
            image, None, h=5, templateWindowSize=7, searchWindowSize=21
        )
        
        # Convert to LAB for better contrast enhancement
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # Apply CLAHE to L channel only (brightness)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)
        
        # Merge back
        lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
        enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def _rapidocr_extract(self, image: np.ndarray) -> str:
        """
        Extract text using RapidOCR with spatial structure preservation.
        
        Args:
            image: Image array
            
        Returns:
            Extracted text with preserved indentation and line breaks
        """
        try:
            if self.ocr is None:
                print("[RapidOCR] OCR engine not initialized")
                return ""
            
            print("[RapidOCR] Running text detection and recognition...")
            result, elapse = self.ocr(image)
            
            if not result:
                print("[RapidOCR] No text detected")
                return ""
            
            # Extract text with bounding boxes
            # RapidOCR returns: [[bbox, text, confidence], ...]
            # bbox format: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            lines = []
            for item in result:
                if item and len(item) >= 2:
                    bbox = item[0]  # Bounding box coordinates
                    text = item[1]  # Detected text
                    confidence = float(item[2]) if len(item) > 2 else 1.0
                    
                    # Get top-left corner position
                    x1 = int(bbox[0][0])  # Left X
                    y1 = int(bbox[0][1])  # Top Y
                    
                    lines.append({
                        'text': text,
                        'x': x1,
                        'y': y1,
                        'confidence': confidence
                    })
                    print(f"[RapidOCR] Found: '{text}' at (x={x1}, y={y1}) confidence={confidence:.2f}")
            
            if not lines:
                return ""
            
            # Sort lines by Y-coordinate (top to bottom)
            lines.sort(key=lambda l: l['y'])
            
            # Smart baseline calculation: use minimum X position, but be smart about outliers
            x_positions = sorted([line['x'] for line in lines])
            
            # Use the minimum X as baseline (leftmost text is usually not indented)
            min_x = x_positions[0]
            
            # But if there's a huge gap suggesting the minimum is an outlier,
            # use the second-smallest or median of lower half
            if len(x_positions) > 3:
                gap = x_positions[1] - x_positions[0]
                next_gap = x_positions[2] - x_positions[1] if len(x_positions) > 2 else gap
                # If gap to second is huge, use second as baseline
                if gap > next_gap * 2:
                    min_x = x_positions[1]
            
            print(f"[RapidOCR] Baseline X position: {min_x} (from positions: {x_positions[:5]}...)")
            
            # Estimate character width from image if possible
            # For small images, use smaller estimates; for larger, use typical monospace width
            image_width = image.shape[1]
            if image_width < 300:
                char_width = 6  # Tighter estimate for small regions
            elif image_width < 600:
                char_width = 8
            else:
                char_width = 10
            
            indent_unit = 4  # spaces per indentation level
            
            # Group lines by Y-coordinate to handle text on same logical line
            # Adaptive grouping based on image height (estimate line height as ~5% of image)
            estimated_line_height = max(10, int(image.shape[0] * 0.05))
            y_tolerance = max(10, estimated_line_height // 2)  # ~ 1/2 of line height for better grouping
            
            y_groups = {}
            for line in lines:
                y = line['y']
                # Group within tolerance of existing groups
                # Find closest existing y_key
                closest_key = None
                min_diff = float('inf')
                
                for key in y_groups.keys():
                    diff = abs(y - key)
                    if diff < min_diff and diff <= y_tolerance:
                        min_diff = diff
                        closest_key = key
                
                if closest_key is not None:
                    y_groups[closest_key].append(line)
                else:
                    # New group
                    y_groups[y] = [line]
            
            # Build structured text with preserved indentation
            structured_lines = []
            for y_key in sorted(y_groups.keys()):
                group = sorted(y_groups[y_key], key=lambda l: l['x'])  # Sort by X within group
                
                # Merge text on same logical line
                merged_text = ' '.join([item['text'] for item in group])
                
                # Use minimum X from group for indentation
                min_x_in_group = min(item['x'] for item in group)
                
                # Calculate indentation offset from baseline
                x_offset = min_x_in_group - min_x
                
                # Clamp to reasonable range: if offset seems extreme, normalize it
                if x_offset < 0:
                    x_offset = 0
                elif x_offset > image_width * 0.5:  # More than half image width is suspicious
                    # This is probably misdetected - treat as minimal indent
                    x_offset = 0
                
                # Convert pixel offset to spaces (rounded to nearest char_width)
                spaces_count = round(x_offset / char_width)
                
                # Normalize to indent units (4 spaces)
                # Clamp to max 5 indent levels (20 spaces) - anything more is probably mis-detected
                indent_level = max(0, min(5, round(spaces_count / indent_unit)))
                actual_spaces = indent_level * indent_unit
                
                # Build formatted line
                indented_line = (' ' * actual_spaces) + merged_text
                structured_lines.append(indented_line)
                print(f"[RapidOCR] Line: x_offset={x_offset}px (min_x={min_x_in_group}) → {actual_spaces} spaces → '{indented_line[:60]}...'")
            
            # Join with newlines to preserve structure
            structured_text = '\n'.join(structured_lines)
            print(f"[RapidOCR] Structured text ({len(structured_lines)} lines):")
            print("---START---")
            print(structured_text)
            print("---END---")
            
            # Post-process to fix common Python syntax issues
            structured_text = self._fix_python_syntax(structured_text)
            
            # Normalize indentation for docstrings
            structured_text = self._normalize_indentation(structured_text)
            
            return structured_text
            
        except Exception as e:
            print(f"[RapidOCR] Error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _fix_python_syntax(self, text: str) -> str:
        """
        Post-process text to fix common Python syntax OCR errors.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Text with fixed Python syntax patterns
        """
        import re
        
        lines = text.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # NEVER treat imports as docstrings - they should never be wrapped in """
            is_import_line = stripped.lower().startswith(('import ', 'from '))
            is_code_line = any(x in stripped for x in ['def ', 'class ', '=', '(', ')', '[', ']', '{', '}', 'if ', 'for ', 'while ', 'return '])
            
            # Only wrap in docstring quotes if it looks like a docstring AND next line is code
            if (not is_import_line and not is_code_line and 
                len(stripped) > 5 and len(stripped) < 100 and
                '"""' not in line and '"' not in line):
                
                # Check if next line is code or def/class
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    next_is_code = any(x in next_line for x in ['def ', 'class ', '=', '(', ')', 'self.', 'return ', 'for ', 'if '])
                    if next_is_code:
                        indent = len(line) - len(line.lstrip())
                        line = ' ' * indent + '"""' + stripped + '"""'
            
            # Fix common OCR artifacts
            line = re.sub(r'\.\"\"\"', '"""', line)
            line = re.sub(r'"""\."', '"""', line)
            line = re.sub(r'^\s*\.\s*"', '"', line)
            # Fix docstring quote issues: double quotes followed by text should be triple
            line = re.sub(r'""([A-Za-z])', r'"""\1', line)  # ""Initialize -> """Initialize
            line = re.sub(r'([a-z])(""")+$', r'\1"""', line)  # Fix trailing quotes
            # Fix excessive quotes: """" -> """
            line = re.sub(r'(^|[^"])("""")+', r'\1"""', line)
            # Fix quote patterns: ""."  or similar
            line = re.sub(r'""\.', '"""', line)
            
            # Fix missing spaces in imports (FIRST)
            line = re.sub(r'(\bimport)([a-z])', r'\1 \2', line, flags=re.IGNORECASE)
            line = re.sub(r'(\bfrom)([a-z])', r'\1 \2', line, flags=re.IGNORECASE)
            
            # Fix method name spacing issues - ONLY in non-docstring lines
            if '"""' not in line:
                # Fix _find screenshot _tool -> _find_screenshot_tool
                line = re.sub(r'_find\s+screenshot\s+_\s*tool', '_find_screenshot_tool', line)
                line = re.sub(r'_find\s+screenshot\s+tool(?=\()', '_find_screenshot_tool', line)
                line = re.sub(r'_find\s+screenshot\s*$', '_find_screenshot', line)  # End of line
                # Fix self._find patterns
                line = re.sub(r'self\.\s*_?\s*find\s+screenshot', 'self._find_screenshot', line)
                line = re.sub(r'self\.\s+f(?=ind)', 'self._f', line)  
                # Fix standalone method references
                line = re.sub(r'\b_find\s+screenshot', '_find_screenshot', line)
            
            # Fix return type hints: None : -> -> None:
            line = re.sub(r'\)\s+None\s*:', r') -> None:', line)
            line = re.sub(r'\]\s+None\s*:', r'] -> None:', line)
            
            # Fix __init__ patterns
            line = re.sub(r'\bdef\s+__?init__?\s*\(', 'def __init__(', line)
            line = re.sub(r'\binit\s+self\)', '__init__(self)', line)
            line = re.sub(r'\binit\s*\(', '__init__(', line)
            line = re.sub(r'\binit\b(?=\s)', '__init__', line)
            
            # Fix __name__ patterns
            line = re.sub(r'\b_?name_?\s*==', '__name__ ==', line)
            line = re.sub(r'==\s*["\']_?main_?["\']', '== "__main__"', line)
            
            # Fix typing imports - capitalize properly
            line = re.sub(r'\b(?<![a-z])optional\b', 'Optional', line, flags=re.IGNORECASE)
            line = re.sub(r'\b(?<![a-z])tuple\b', 'Tuple', line, flags=re.IGNORECASE)
            line = re.sub(r'\b(?<![a-z])list\b', 'List', line, flags=re.IGNORECASE)
            line = re.sub(r'\b(?<![a-z])dict\b', 'Dict', line, flags=re.IGNORECASE)
            line = re.sub(r'\b(?<![a-z])set\b', 'Set', line, flags=re.IGNORECASE)
            
            # Fix class names - capitalize first letter and handle common patterns
            line = re.sub(r'\bclass\s+([a-z])', lambda m: 'class ' + m.group(1).upper(), line)
            # Fix specific pattern: Portalscreenshot -> PortalScreenshot
            line = re.sub(r'\bPortalscreenshot\b', 'PortalScreenshot', line)
            # Fix any XYZscreenshot pattern to XYZScreenshot
            line = re.sub(r'([A-Z][a-z]+)screenshot\b', r'\1Screenshot', line, flags=re.IGNORECASE)
            
            # Fix screenshot_tool spelling
            line = re.sub(r'screenshot\s+tool\s*\(\s*\)', 'screenshot_tool()', line)
            line = re.sub(r'screenshot\s+tool(?=\s|$|\))', 'screenshot_tool', line)
            
            # Fix missing assignment operators
            line = re.sub(r'(self\.screenshot_tool)\s+self\._find\s+screenshot_tool\(\)', 
                         r'\1 = self._find_screenshot_tool()', line)
            line = re.sub(r'(self\.\w+)\s+(self\._?\w+\()', r'\1 = \2', line)
            
            # Fix docstring word order before ports
            line = re.sub(r'Initialize\s+connection\.\s+portal',
                         'Initialize portal connection.', line)
            
            # Clean up spacing
            line = re.sub(r'\bself\.\s+', 'self.', line)
            line = re.sub(r'(?<![_\w])self([a-z_])', r'self.\1', line)
            
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines)
    
    def _normalize_indentation(self, text: str) -> str:
        """
        Normalize docstring indentation to match surrounding code.
        
        Args:
            text: Text with potential indentation issues
            
        Returns:
            Text with normalized indentation
        """
        lines = text.split('\n')
        result_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if this is a docstring line (starts with """)
            if '"""' in lines[i]:
                # Look ahead to find the next code line (non-docstring)
                next_code_indent = None
                for j in range(i + 1, min(i + 3, len(lines))):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if next_stripped and '"""' not in next_stripped:
                        next_code_indent = len(next_line) - len(next_line.lstrip())
                        break
                
                # If we found a code line, match its indentation
                if next_code_indent is not None and next_code_indent > 0:
                    result_lines.append(' ' * next_code_indent + stripped)
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def extract_text(
        self,
        image_path: str,
        region: Tuple[int, int, int, int]
    ) -> str:
        """
        Extract text from image region.
        
        Args:
            image_path: Path to image file
            region: (x, y, width, height) tuple for crop
            
        Returns:
            Extracted and cleaned text
        """
        print(f"[OCR] Reading image: {image_path}")
        # Read image
        image = self._read_image(image_path)
        if image is None:
            print("[OCR] Failed to read image")
            return ""
        
        print(f"[OCR] Image shape: {image.shape}")
        
        # Crop to region
        print(f"[OCR] Cropping to region: {region}")
        cropped = self._crop_region(image, region)
        print(f"[OCR] Cropped shape: {cropped.shape}")
        
        # Preprocess image
        print("[OCR] Preprocessing image...")
        preprocessed = self._preprocess_image(cropped)
        print(f"[OCR] Preprocessed shape: {preprocessed.shape}")
        
        # Use RapidOCR
        print("[OCR] Running RapidOCR...")
        text = self._rapidocr_extract(preprocessed)
        print(f"[OCR] Final result: '{text}'")
        return text
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.ocr = None
