import cv2
import numpy as np
from ocr_engine import OCREngine
from PIL import Image, ImageDraw, ImageFont

# Create a dummy image
img = Image.new('RGB', (800, 400), color=(30, 30, 30))
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("DejaVuSansMono.ttf", 20)
except:
    font = ImageFont.load_default()

code = """def foo():
    if True:
        print("bar")
"""
d.text((50, 50), code, fill=(200, 200, 200), font=font)
img.save("test_code.png")

engine = OCREngine()
print(engine.extract_text("test_code.png"))
