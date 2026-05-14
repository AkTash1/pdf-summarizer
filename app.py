import streamlit as st
import subprocess
import pytesseract

st.title("Debug")

result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
result2 = subprocess.run(['find', '/usr', '-name', 'tesseract'], capture_output=True, text=True)
result3 = subprocess.run(['find', '/', '-name', 'tesseract', '-type', 'f'], capture_output=True, text=True)

st.write("which:", result.stdout or "NOT FOUND")
st.write("find /usr:", result2.stdout or "NOT FOUND")
st.write("find /:", result3.stdout or "NOT FOUND")
