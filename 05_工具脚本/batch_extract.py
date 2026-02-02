import os
from pypdf import PdfReader

def extract_to_md(pdf_path, md_path):
    print(f"Extracting: {pdf_path} -> {md_path}")
    try:
        reader = PdfReader(pdf_path)
        content = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                content.append(f"## Page {i+1}\n\n{text}\n")
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {os.path.basename(pdf_path)}\n\n")
            f.write("\n".join(content))
        return True
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return False

base_dirs = [
    "/Users/huangyijun/Desktop/Academic/Papers/With You/Thesis/百戏与傩仪、傩戏/",
    "/Users/huangyijun/Desktop/Academic/Papers/With You/Thesis/鱼龙/"
]

for d in base_dirs:
    if not os.path.exists(d):
        continue
    for file in os.listdir(d):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(d, file)
            md_path = os.path.join(d, file.replace(".pdf", ".md"))
            extract_to_md(pdf_path, md_path)

print("\n--- All tasks completed ---")
