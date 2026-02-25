"""
从绪论正文中提取所有提到的文献引用。
输出分类列表供手工校对。
"""
import re
from docx import Document

def extract_refs_from_intro(docx_path):
    doc = Document(docx_path)

    # 绪论正文段落49-127
    intro_text = ''
    for i in range(49, 128):
        intro_text += doc.paragraphs[i].text.strip() + '\n'

    # 提取模式1: 作者《书/文名》（出版社/刊名，年份年）
    pattern1 = re.findall(r'([^，。、；\n]{2,20})(?:的|在其)?《([^》]+)》[（(]([^）)]+)[）)]', intro_text)

    # 提取模式2: 作者《书/文名》（年份年）
    pattern2 = re.findall(r'([^，。、；\n]{2,20})(?:的|在其)?《([^》]+)》[（(](\d{4}年)[）)]', intro_text)

    # 提取模式3: 《书名》（出版社，年份）
    pattern3 = re.findall(r'《([^》]+)》[（(]([^）)]+出版[^）)]*)[）)]', intro_text)

    # 提取模式4: 作者《篇名》（《刊名》，年份年第X期）
    pattern4 = re.findall(r'([^，。、；\n]{2,15})《([^》]+)》[（(]《([^》]+)》[，,]?\s*(\d{4})年[^）)]*[）)]', intro_text)

    # 提取模式5: 硕博论文 作者《题目》（学校硕/博士论文，年份年）
    pattern5 = re.findall(r'([^，。、；\n]{2,10})(?:的|在其)?《([^》]+)》[（(]([^）)]*(?:硕士|博士)[^）)]*)[）)]', intro_text)

    print("=" * 70)
    print("从绪论正文提取的文献引用")
    print("=" * 70)

    all_refs = set()

    print("\n--- 模式1: 作者《书/文名》（出版信息） ---")
    for author, title, pub_info in pattern1:
        author = author.strip().lstrip('如在的').strip()
        ref = f"{author}：《{title}》（{pub_info}）"
        if ref not in all_refs:
            all_refs.add(ref)
            print(f"  {ref}")

    print(f"\n--- 模式4: 期刊论文 ---")
    for author, title, journal, year in pattern4:
        author = author.strip().lstrip('如在的').strip()
        ref = f"{author}：《{title}》，《{journal}》，{year}年"
        if ref not in all_refs:
            all_refs.add(ref)
            print(f"  {ref}")

    print(f"\n--- 模式5: 学位论文 ---")
    for author, title, info in pattern5:
        author = author.strip().lstrip('如在的').strip()
        ref = f"{author}：《{title}》（{info}）"
        if ref not in all_refs:
            all_refs.add(ref)
            print(f"  {ref}")

    print(f"\n\n共提取 {len(all_refs)} 条（去重后）")


if __name__ == '__main__':
    extract_refs_from_intro('郑璎_《汉唐百戏书写研究》二稿参考文献1_20260225_脚注规范化.docx')
