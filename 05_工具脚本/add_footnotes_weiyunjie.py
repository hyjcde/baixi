import docx
from pathlib import Path
from lxml import etree
import copy

INFILE = Path("/Users/huangyijun/Desktop/个人文件/宝资料/学术论文/Thesis/第二章_杂技历史书写（汉至隋唐）_博士论文修改版.docx")
doc = docx.Document(str(INFILE))

# Find the footnotes part
footnotes_part = None
for rel in doc.part.rels.values():
    if "footnotes" in rel.reltype:
        footnotes_part = rel.target_part
        break

if not footnotes_part:
    print("Error: footnotes_part not found.")
    exit(1)

tree = etree.fromstring(footnotes_part.blob)
w_ns = tree.nsmap.get('w')

# Find max footnote ID
existing_ids = [int(f.get(f'{{{w_ns}}}id')) for f in tree.findall(f'.//{{{w_ns}}}footnote') if f.get(f'{{{w_ns}}}id')]
next_id = max(existing_ids) + 1 if existing_ids else 1

mappings = [
    ("秦汉文献中常将“角抵”与“百戏”混用或并提", "参见魏云洁：《中国古代宴乐的交流功能研究》，四川大学博士学位论文，2021年，第75页。"),
    ("百戏作为以视觉为主的宴乐演出", "参见魏云洁：《中国古代宴乐的交流功能研究》，四川大学博士学位论文，2021年，第96页。"),
    ("汉代宴享用乐在制度上常归入“黄门鼓吹”或“散乐”名下", "相关概念辨析参见魏云洁：《中国古代宴乐的交流功能研究》，四川大学博士学位论文，2021年，第72、105页。"),
    ("隋唐时百戏在宴乐中的“重兴”除正史与《教坊记》外", "参见魏云洁：《中国古代宴乐的交流功能研究》，四川大学博士学位论文，2021年，第170-172页。"),
    ("这种带有明确写作构思与情感引导的记述表明", "参见魏云洁：《中国古代宴乐的交流功能研究》，四川大学博士学位论文，2021年，第106、189页。"),
    ("书写者不再仅仅作为事实的客观记录者", "参见魏云洁：《中国古代宴乐的交流功能研究》，四川大学博士学位论文，2021年，第190页。")
]

def create_footnote_element(fn_id, text, w_ns):
    # Construct an XML string and parse it.
    xml_str = f'''
    <w:footnote xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:id="{fn_id}">
        <w:p>
            <w:pPr>
                <w:pStyle w:val="a40"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:rStyle w:val="a30"/>
                </w:rPr>
                <w:footnoteRef/>
            </w:r>
            <w:r>
                <w:t xml:space="preserve"> </w:t>
            </w:r>
            <w:r>
                <w:t>{text}</w:t>
            </w:r>
        </w:p>
    </w:footnote>
    '''
    return etree.fromstring(xml_str.encode('utf-8'))

# First, modify doc paragraphs
added_footnotes = 0

for p in doc.paragraphs:
    text = p.text.strip()
    if not text: continue
    
    for target, fn_text in mappings:
        if target in text:
            # Check if this paragraph already has a footnote reference to avoid duplicates
            has_ref = False
            for r in p._element.findall(f'.//{{{w_ns}}}footnoteReference'):
                has_ref = True
            
            if not has_ref:
                # Add to tree
                fn_elem = create_footnote_element(next_id, fn_text, w_ns)
                tree.append(fn_elem)
                
                # We want to insert the footnote reference at the end of the red text run
                # The red text might be split into multiple runs. We find the last run containing part of the target or just append to paragraph.
                # It's safest to just append to the end of the paragraph's runs.
                ref_xml = f'''
                <w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                    <w:rPr>
                        <w:rStyle w:val="a30"/>
                    </w:rPr>
                    <w:footnoteReference w:id="{next_id}"/>
                </w:r>
                '''
                ref_elem = etree.fromstring(ref_xml.encode('utf-8'))
                p._element.append(ref_elem)
                
                print(f"Added footnote {next_id} for: {target[:15]}...")
                next_id += 1
                added_footnotes += 1
            break

if added_footnotes > 0:
    # Update the blob
    footnotes_part._blob = etree.tostring(tree, xml_declaration=True, standalone="yes")
    doc.save(str(INFILE))
    print(f"Saved {added_footnotes} footnotes to {INFILE.name}.")
else:
    print("No new footnotes needed.")
