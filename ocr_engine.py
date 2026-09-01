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
        # Add padding to help OCR detect text at the very edges (for tight crops)
        # Use the median pixel color of the image as the background fill, since text is the minority
        bg_color = np.median(image, axis=(0, 1)).astype(int).tolist()
        image = cv2.copyMakeBorder(image, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=bg_color)
        
        # Upscale (2.0x) to ensure faint grey docstrings 
        # and thin punctuation are easily readable by the OCR engine.
        height, width = image.shape[:2]
        scale = 2.0
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Return the upscaled image directly
        # Aggressive denoising or contrast adjustments often blur small punctuation like """ or :
        return image
    
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
            
            # Use the absolute minimum X as baseline
            x_positions = sorted([line['x'] for line in lines])
            min_x = x_positions[0]
            
            print(f"[RapidOCR] Baseline X position: {min_x} (from positions: {x_positions[:5]}...)")
            
            # Dynamically estimate character width based on actual indentations
            # Find all positive X offsets relative to min_x
            x_offsets = sorted([x - min_x for x in x_positions if x - min_x > 15])
            
            image_width = image.shape[1]
            if x_offsets:
                # Group offsets into clusters (e.g. 4-space, 8-space indents)
                clusters = []
                current_cluster = [x_offsets[0]]
                for x in x_offsets[1:]:
                    # If within 15 pixels, it's the same indentation level
                    if x - current_cluster[-1] < 15:
                        current_cluster.append(x)
                    else:
                        clusters.append(current_cluster)
                        current_cluster = [x]
                clusters.append(current_cluster)
                
                # To avoid single-character noise, find the first cluster with >1 item, 
                # or fallback to the largest cluster if all have 1 item.
                valid_clusters = [c for c in clusters if len(c) > 1]
                if valid_clusters:
                    first_indent_cluster = valid_clusters[0]
                else:
                    first_indent_cluster = max(clusters, key=len)
                    
                import numpy as np
                first_indent = float(np.median(first_indent_cluster))
                char_width = first_indent / 4.0
                print(f"[RapidOCR] Dynamic char_width: {char_width:.2f} (based on 1st indent cluster median: {first_indent}px, size: {len(first_indent_cluster)})")
            else:
                if image_width < 300:
                    char_width = 6.0
                elif image_width < 600:
                    char_width = 8.0
                else:
                    char_width = 10.0
                print(f"[RapidOCR] Fallback char_width: {char_width}")
            
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
                
                # Convert pixel offset to spaces (rounded to nearest integer)
                spaces_count = int(round(x_offset / char_width))
                
                # Clamp to max 30 spaces - anything more is probably mis-detected
                spaces_count = max(0, min(30, spaces_count))
                
                # Build formatted line
                indented_line = (' ' * spaces_count) + merged_text
                structured_lines.append(indented_line)
                print(f"[RapidOCR] Line: x_offset={x_offset}px (min_x={min_x_in_group}) → {spaces_count} spaces → '{indented_line[:60]}...'")
            
            # Join with newlines to preserve structure
            structured_text = '\n'.join(structured_lines)
            print(f"[RapidOCR] Structured text ({len(structured_lines)} lines):")
            print("---START---")
            print(structured_text)
            print("---END---")
            
            # Fix known RapidOCR hallucination where """ is misread as 1 11 or 11 11 11
            import re
            structured_text = re.sub(r'^( *)(?:1\s*11|11\s*11\s*11|11\s*11|1\s*1|""\s*11|11\s*"")\s*$', r'\1"""', structured_text, flags=re.MULTILINE)
            
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
            
            # We used to have artificial logic here to wrap lines in """ if they didn't look like code.
            # This was removed because it caused false positives like """Returns:""".
            # It's better to rely on RapidOCR's """ detection or the 1 11 regex fix.
            
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
            
            # Fix XML/HTML tag hallucinations
            # OCR often sees `<` as `c` and `</` as `cr` or `k/`
            line = re.sub(r'^(\s*)c([A-Z][A-Za-z]+>)', r'\1<\2', line)
            line = re.sub(r'^(\s*)cr([A-Z][A-Za-z]+>)', r'\1</\2', line)
            line = re.sub(r'k/([A-Z][A-Za-z]+>)', r'</\1', line)
            line = re.sub(r'iten/([A-Z][A-Za-z]+>)', r'item</\1', line)
            
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
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> str:
        """
        Extract text from image region.
        
        Args:
            image_path: Path to image file
            region: Optional (x, y, width, height) tuple for crop. If None, uses full image.
            
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
        
        # Crop to region if specified
        if region is not None:
            print(f"[OCR] Cropping to region: {region}")
            cropped = self._crop_region(image, region)
            print(f"[OCR] Cropped shape: {cropped.shape}")
        else:
            cropped = image
            print("[OCR] Using full image (no crop)")
        
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
