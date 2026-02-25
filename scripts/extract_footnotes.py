"""Extract all footnotes from the thesis docx file and print them."""
import sys
from docx import Document
from lxml import etree

def extract_footnotes(docx_path):
    doc = Document(docx_path)
    
    footnotes_part = None
    for rel in doc.part.rels.values():
        if "footnotes" in rel.reltype:
            footnotes_part = rel.target_part
            break
    
    if footnotes_part is None:
        print("No footnotes found.")
        return []
    
    nsmap = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    }
    
    root = etree.fromstring(footnotes_part.blob)
    footnotes = root.findall('.//w:footnote', nsmap)
    
    results = []
    for fn in footnotes:
        fn_id = fn.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
        if fn_id in ('0', '-1'):
            continue
        
        texts = []
        for t in fn.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t.text:
                texts.append(t.text)
        
        full_text = ''.join(texts).strip()
        if full_text:
            results.append((fn_id, full_text))
    
    return results

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '郑璎_《汉唐百戏书写研究》二稿参考文献1_20260225.docx'
    footnotes = extract_footnotes(path)
    print(f"Total footnotes: {len(footnotes)}\n")
    for fn_id, text in footnotes:
        print(f"[{fn_id}] {text}")
