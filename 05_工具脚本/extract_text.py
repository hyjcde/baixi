from pdfminer.high_level import extract_text
import os

files = [
    "“早期戏剧史料”新探——以隋唐至两宋类书为中心_黎国韬.pdf",
    "东汉禁中大傩仪执事官考_黎国韬.pdf",
    "汉唐百戏管理机构考_黎国韬.pdf",
    "秦汉假人傀儡戏述论_黎国韬.pdf"
]

base_path = "/Users/huangyijun/Desktop/Academic/Papers/With You/Thesis/百戏与傩仪、傩戏/"

for f in files:
    full_path = os.path.join(base_path, f)
    print(f"\n--- Processing: {f} ---")
    try:
        text = extract_text(full_path)
        # 搜索包含“百戏”或“傩”的行
        lines = text.split('\n')
        relevant_content = []
        for i, line in enumerate(lines):
            if "百戏" in line or "傩" in line:
                # 抓取上下两行作为上下文
                start = max(0, i-2)
                end = min(len(lines), i+3)
                relevant_content.append("\n".join(lines[start:end]))
        
        if relevant_content:
            print("\n".join(relevant_content[:15])) # 每个文件展示前15个相关片段
        else:
            print("No matching text found (might be a scanned image or no text layer).")
    except Exception as e:
        print(f"Error: {e}")
