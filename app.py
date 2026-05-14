import streamlit as st
import subprocess
import sys

# Force install tesseract at runtime
subprocess.run(['apt-get', 'update'], capture_output=True)
subprocess.run(['apt-get', 'install', '-y', 'tesseract-ocr'], capture_output=True)

import pytesseract
from PIL import Image

result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
st.write("tesseract path:", result.stdout or "still not found")
