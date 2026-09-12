import sys
from docx import Document

try:
    doc = Document(r"/downloads/Template TCC - Implementação de Algoritmo(s) de Machine Learning (251, 252).docx")
    for p in doc.paragraphs:
        if p.text.strip():
            print(p.text)
except Exception as e:
    print(f"Error: {e}")
