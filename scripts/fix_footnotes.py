#!/usr/bin/env python3
"""
脚注格式修复脚本
功能：
1. 去除脚注前的空行（段前间距设为0）
2. 设置脚注字体：中文宋体，英文Times New Roman
3. 设置脚注字号：10pt
"""

import zipfile
import shutil
import os
from lxml import etree
from datetime import datetime
import sys

def fix_footnotes(input_docx, output_docx=None):
    """
    修复docx文件中的脚注格式
    
    Args:
        input_docx: 输入的docx文件路径
        output_docx: 输出的docx文件路径（可选，默认生成新版本）
    """
    
    if output_docx is None:
        version = datetime.now().strftime("%Y%m%d_%H%M")
        base_name = os.path.splitext(input_docx)[0]
        output_docx = f"{base_name}_fixed_{version}.docx"
    
    # 复制原文件
    shutil.copy(input_docx, output_docx)
    
    # 临时目录
    temp_dir = f"temp_docx_{datetime.now().strftime('%H%M%S')}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # 解压docx
        with zipfile.ZipFile(output_docx, 'r') as z:
            z.extractall(temp_dir)
        
        # 命名空间
        nsmap = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        }
        
        # 修改footnotes.xml
        footnotes_path = os.path.join(temp_dir, 'word', 'footnotes.xml')
        if os.path.exists(footnotes_path):
            tree = etree.parse(footnotes_path)
            root = tree.getroot()
            
            footnote_count = 0
            
            # 遍历所有脚注
            for footnote in root.findall('.//w:footnote', nsmap):
                footnote_count += 1
                
                # 遍历脚注中的段落
                for para in footnote.findall('.//w:p', nsmap):
                    pPr = para.find('w:pPr', nsmap)
                    if pPr is None:
                        pPr = etree.SubElement(para, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr')
                        para.insert(0, pPr)
                    
                    # 设置段落间距为0
                    spacing = pPr.find('w:spacing', nsmap)
                    if spacing is None:
                        spacing = etree.SubElement(pPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing')
                    spacing.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}before', '0')
                    spacing.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}after', '0')
                    spacing.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}line', '240')  # 单倍行距
                    
                    # 遍历所有run，设置字体
                    for run in para.findall('.//w:r', nsmap):
                        rPr = run.find('w:rPr', nsmap)
                        if rPr is None:
                            rPr = etree.SubElement(run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
                            run.insert(0, rPr)
                        
                        # 设置字体
                        rFonts = rPr.find('w:rFonts', nsmap)
                        if rFonts is None:
                            rFonts = etree.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts')
                        
                        rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii', 'Times New Roman')
                        rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi', 'Times New Roman')
                        rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia', '宋体')
                        rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs', 'Times New Roman')
                        
                        # 设置字号（10pt = 20半点）
                        sz = rPr.find('w:sz', nsmap)
                        if sz is None:
                            sz = etree.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
                        sz.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '20')
                        
                        szCs = rPr.find('w:szCs', nsmap)
                        if szCs is None:
                            szCs = etree.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}szCs')
                        szCs.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '20')
                        
                        # 移除斜体
                        italic = rPr.find('w:i', nsmap)
                        if italic is not None:
                            rPr.remove(italic)
                        
                        # 设置颜色为黑色
                        color = rPr.find('w:color', nsmap)
                        if color is None:
                            color = etree.SubElement(rPr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                        color.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '000000')
            
            # 保存修改后的footnotes.xml
            tree.write(footnotes_path, xml_declaration=True, encoding='UTF-8', standalone=True)
            print(f"已处理 {footnote_count} 个脚注")
        else:
            print("警告：文档中没有找到脚注")
        
        # 重新打包docx
        with zipfile.ZipFile(output_docx, 'w', zipfile.ZIP_DEFLATED) as z:
            for root_dir, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    z.write(file_path, arcname)
        
        print(f"已生成: {output_docx}")
        print("脚注设置：")
        print("  - 段前间距: 0")
        print("  - 段后间距: 0")
        print("  - 中文字体: 宋体")
        print("  - 英文字体: Times New Roman")
        print("  - 字号: 10pt")
        
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    return output_docx


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python fix_footnotes.py <input.docx> [output.docx]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_footnotes(input_file, output_file)
