"""
Utility functions for OCR application.
"""
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, unquote


def parse_portal_response(response: dict) -> Optional[str]:
    """
    Parse XDG Desktop Portal Screenshot response and extract file path.
    
    Args:
        response: Dictionary response from portal Screenshot method
        
    Returns:
        Local file path or None if parsing failed
    """
    try:
        if not isinstance(response, dict):
            return None
            
        # Portal returns a dict with 'uris' key containing a list of URIs
        uris = response.get('uris', [])
        if not uris:
            return None
            
        uri = uris[0]
        # Convert file:// URI to local path
        parsed = urlparse(uri)
        file_path = unquote(parsed.path)
        
        if os.path.exists(file_path):
            return file_path
        return None
    except Exception:
        return None


def clean_ocr_text(text: str) -> str:
    """
    Clean OCR output text while preserving structure.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text with preserved line breaks and indentation
    """
    if not text:
        return ""
    
    # Split into lines to process individually
    lines = text.split('\n')
    
    # Clean each line while preserving leading spaces
    cleaned_lines = []
    for line in lines:
        # Remove trailing whitespace but keep leading spaces (indentation)
        line = line.rstrip()
        # Replace multiple spaces (not at start) with single space
        # But preserve indentation at the start
        if line.lstrip():  # If line has content
            # Get leading spaces
            leading_spaces = len(line) - len(line.lstrip())
            content = line.lstrip()
            # Clean content part only
            content = re.sub(r' +', ' ', content)
            line = (' ' * leading_spaces) + content
        cleaned_lines.append(line)
    
    # Remove excessive blank lines (more than 1 consecutive)
    result = []
    prev_blank = False
    for line in cleaned_lines:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue  # Skip multiple consecutive blank lines
        result.append(line)
        prev_blank = is_blank
    
    return '\n'.join(result)


def ensure_cache_dir() -> Path:
    """
    Ensure cache directory exists for temporary files.
    
    Returns:
        Path to cache directory
    """
    cache_dir = Path.home() / '.cache' / 'wayland-ocr'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
