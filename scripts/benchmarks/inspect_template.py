import sys
from docx import Document

try:
    doc = Document(r"/downloads/Template TCC - Implementação de Algoritmo(s) de Machine Learning (251, 252).docx")
    for i, p in enumerate(doc.paragraphs[:20]):
        print(f"[{i}]: {p.text}")
except Exception as e:
    print(f"Error: {e}")
