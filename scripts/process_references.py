"""
从论文docx提取脚注，规范格式，生成参考文献列表，并修改脚注。
参考文献按经史子集分类，每类内按年代排序。
总纲：古籍文献（经/史/子/集）→ 今人专著 → 期刊论文 → 学位论文
"""
import sys
import re
import copy
from collections import defaultdict
from docx import Document
from lxml import etree

NSMAP = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

DYNASTY_ORDER = {
    '春秋': 1, '战国': 2, '秦': 3, '汉': 4, '西汉': 4, '东汉': 5,
    '三国': 6, '三国魏': 6, '魏': 6, '蜀': 6, '吴': 6,
    '西晋': 7, '东晋': 7, '晋': 7,
    '十六国': 8, '北凉': 8,
    '南朝宋': 9, '南朝齐': 10, '南朝梁': 11, '南朝陈': 12,
    '南朝': 10, '梁': 11, '陈': 12,
    '北魏': 13, '东魏': 14, '西魏': 14, '北齐': 15, '北周': 15,
    '隋': 16, '唐': 17, '五代': 18, '后晋': 18, '后唐': 18,
    '宋': 19, '北宋': 19, '南宋': 20,
    '辽': 19, '金': 20, '元': 21, '明': 22, '清': 23,
    '新罗': 17,
    '原题': 0,
}


def extract_footnotes(docx_path):
    """提取所有脚注文本"""
    doc = Document(docx_path)
    footnotes_part = None
    for rel in doc.part.rels.values():
        if "footnotes" in rel.reltype:
            footnotes_part = rel.target_part
            break
    if footnotes_part is None:
        return []
    
    root = etree.fromstring(footnotes_part.blob)
    footnotes = root.findall('.//w:footnote', NSMAP)
    
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


def normalize_footnote(text):
    """规范化单条脚注格式，去掉[M][J][D]等标记"""
    text = re.sub(r'\[M\d*\]', '', text)
    text = re.sub(r'\[J\]', '', text)
    text = re.sub(r'\[D\]', '', text)
    text = re.sub(r'\[C\]', '', text)
    text = re.sub(r'\[A\]', '', text)
    text = re.sub(r'\[G\]', '', text)
    text = re.sub(r'\[Z\]', '', text)
    text = re.sub(r'\[Ｍ\]', '', text)
    text = re.sub(r'[．]', '，', text)  # 全角句点改逗号
    # 统一标点
    text = text.replace(':', '：').replace(',', '，')
    # 去除多余空格
    text = re.sub(r'\s+', '', text)
    # 恢复必要空格 - 在英文单词间
    return text.strip()


def is_citation_footnote(text):
    """判断是否为文献引用型脚注（而非说明性脚注）"""
    if text.startswith('同上'):
        return False
    if text.startswith('？') or text == '？':
        return False
    if '《' in text and ('出版' in text or '书局' in text or '年版' in text or '年，' in text or '年。' in text):
        return True
    if re.search(r'\[\w+\]', text) and '《' in text:
        return True
    return False


def parse_citation(text):
    """解析一条引用，提取关键信息"""
    info = {
        'original': text,
        'dynasty': '',
        'author': '',
        'book': '',
        'publisher': '',
        'year': '',
        'city': '',
        'type': 'unknown',
    }
    
    # 提取朝代和作者 - [朝代]作者
    dynasty_match = re.search(r'[\[［【（(]([^）)\]］】]+)[\]］】）)]([^：:《\[［【（(，,]+)', text)
    if dynasty_match:
        info['dynasty'] = dynasty_match.group(1).strip()
        info['author'] = dynasty_match.group(2).strip()
    else:
        # 无朝代标记的现代作者
        author_match = re.match(r'^([^：:《\[［【（(，,]{1,10})[：:]', text)
        if author_match:
            info['author'] = author_match.group(1).strip()
    
    # 提取书名 - 《...》
    book_match = re.search(r'《([^》]+)》', text)
    if book_match:
        info['book'] = book_match.group(1)
    
    # 提取出版社
    pub_match = re.search(r'([\u4e00-\u9fa5]+出版[\u4e00-\u9fa5]*|[\u4e00-\u9fa5]+书局|[\u4e00-\u9fa5]+书院|[\u4e00-\u9fa5]+印书馆)', text)
    if pub_match:
        info['publisher'] = pub_match.group(1)
    
    # 提取年份
    year_match = re.search(r'(\d{4})\s*年', text)
    if year_match:
        info['year'] = year_match.group(1)
    
    # 提取城市
    city_match = re.search(r'[，,]([^，,：:]{2,6})[：:]', text)
    if city_match:
        city_candidate = city_match.group(1).strip()
        cities = ['北京', '上海', '天津', '重庆', '南京', '杭州', '广州', '武汉',
                  '成都', '西安', '长沙', '沈阳', '济南', '台北', '首尔', '桂林',
                  '长春', '哈尔滨', '石家庄', '郑州', '合肥', '福州', '南昌',
                  '太原', '兰州', '昆明', '贵阳', '海口', '银川', '西宁',
                  '呼和浩特', '乌鲁木齐', '拉萨', '中国台北']
        for c in cities:
            if c in text:
                info['city'] = c
                break
    
    # 判断文献类型
    if info['dynasty'] and info['dynasty'] in DYNASTY_ORDER:
        info['type'] = 'ancient'
    elif '期' in text or '第.*期' in text:
        info['type'] = 'journal'
    elif '学位' in text or '硕士' in text or '博士' in text:
        info['type'] = 'thesis'
    elif info['author'] and not info['dynasty']:
        info['type'] = 'modern_book'
    
    return info


def classify_ancient(book_name, text):
    """将古籍按经史子集分类"""
    jing_keywords = ['经', '易', '诗', '书', '礼', '春秋', '论语', '孟子', '尔雅',
                     '周礼', '仪礼', '公羊', '穀梁', '左传', '孝经',
                     '十三经', '毛诗', '尚书', '礼记', '周易']
    shi_keywords = ['史记', '汉书', '后汉书', '三国志', '晋书', '宋书', '南齐书',
                    '梁书', '陈书', '魏书', '北齐书', '周书', '隋书', '南史', '北史',
                    '旧唐书', '新唐书', '旧五代史', '新五代史', '宋史',
                    '辽史', '金史', '元史', '明史',
                    '资治通鉴', '通鉴', '通典', '文献通考', '续通典',
                    '唐会要', '册府元龟',
                    '西京杂记', '洛阳伽蓝记', '大唐西域记',
                    '邺中记', '安禄山事迹', '明皇杂录',
                    '因话录', '封氏闻见记', '朝野佥载', '独异志',
                    '南部新书', '教坊记', '尚书故实', '杜阳杂编',
                    '东京梦华录', '梦粱录', '中朝故事',
                    '唐音癸签', '战国策', '风俗通义', '四民月令',
                    '荆楚岁时记', '岁时广记', '古今岁时杂咏', '玉烛宝典',
                    '汉官典职', '汉官六种', '玉海',
                    '睡虎地秦墓竹简',
                    '太平广记', '太平御览',
                    '酉阳杂俎', '幻异志', '幻戏志', '玄怪录',
                    '搜神记', '拾遗记', '列女传']
    zi_keywords = ['子', '庄子', '老子', '韩非子', '荀子', '墨子',
                   '管子', '淮南子', '吕氏春秋', '列子',
                   '说文解字', '广韵',
                   '论衡', '抱朴子', '颜氏家训',
                   '新编诸子集成', '诸子集成',
                   '山海经', '春秋繁露',
                   '高僧传', '法苑珠林', '大正藏', '大方等大集经',
                   '佛说太子瑞应本起经',
                   '法藏碎金录']
    ji_keywords = ['文选', '六臣注文选', '文心雕龙',
                   '全唐诗', '全唐文', '全上古三代秦汉三国六朝文',
                   '先秦汉魏晋南北朝诗',
                   '艺文类聚', '初学记', '古文苑',
                   '诗品', '曹植集', '玉台新咏',
                   '桂苑笔耕集',
                   '赋', '诗']

    for kw in jing_keywords:
        if kw in book_name:
            return 'jing'
    for kw in shi_keywords:
        if kw in book_name:
            return 'shi'
        if kw in text:
            return 'shi'
    for kw in zi_keywords:
        if kw in book_name:
            return 'zi'
    for kw in ji_keywords:
        if kw in book_name:
            return 'ji'
    
    if '赋' in book_name or '诗' in book_name or '歌' in book_name or '行' in book_name:
        return 'ji'
    
    return 'shi'


def dynasty_sort_key(info):
    """按朝代排序的键"""
    d = info.get('dynasty', '')
    order = DYNASTY_ORDER.get(d, 99)
    year = int(info.get('year', '9999')) if info.get('year', '').isdigit() else 9999
    return (order, year, info.get('author', ''))


def format_reference_for_list(info):
    """
    将文献信息格式化为参考文献列表的格式。
    古籍格式：[朝代]作者撰：《书名》，城市：出版社，年份年。
    不包含具体卷数和页码。
    """
    parts = []
    if info['dynasty']:
        parts.append(f"[{info['dynasty']}]")
    
    author = info['author']
    if author:
        # 去掉作者后面可能跟的"撰"、"编"等字
        parts.append(author)
    
    if info['book']:
        # 去掉卷数信息
        book_clean = re.sub(r'卷[^，,》]*', '', info['book']).strip()
        book_clean = re.sub(r'[篇章节].*$', '', book_clean).strip()
        parts.append(f"：《{book_clean}》")
    
    if info['city'] and info['publisher']:
        parts.append(f"，{info['city']}：{info['publisher']}")
    elif info['publisher']:
        parts.append(f"，{info['publisher']}")
    
    if info['year']:
        parts.append(f"，{info['year']}年。")
    else:
        parts.append("。")
    
    result = ''.join(parts)
    # 清理重复的标点
    result = result.replace('，，', '，')
    result = result.replace('。。', '。')
    return result


def deduplicate_by_book(citations):
    """按书名去重，保留信息最完整的版本"""
    seen = {}
    for info in citations:
        book = info.get('book', '')
        if not book:
            continue
        # 简化书名用于比较（去掉卷数）
        book_key = re.sub(r'卷[^》]*', '', book).strip()
        book_key = re.sub(r'[（(].*[）)]', '', book_key).strip()
        
        if book_key in seen:
            existing = seen[book_key]
            # 保留信息更完整的
            if len(info['original']) > len(existing['original']):
                seen[book_key] = info
        else:
            seen[book_key] = info
    
    return list(seen.values())


def process_all(docx_path):
    """主处理流程"""
    footnotes = extract_footnotes(docx_path)
    print(f"提取到 {len(footnotes)} 条脚注\n")
    
    all_citations = []
    skipped = []
    
    for fn_id, text in footnotes:
        normalized = normalize_footnote(text)
        
        if not is_citation_footnote(text):
            skipped.append((fn_id, text[:50]))
            continue
        
        # 有些脚注包含多条引用（用分号分隔），需要拆分
        # 但这里先作为整体处理
        info = parse_citation(text)
        info['fn_id'] = fn_id
        if info['book']:
            all_citations.append(info)
    
    print(f"识别出 {len(all_citations)} 条文献引用")
    print(f"跳过 {len(skipped)} 条非引用脚注\n")
    
    # 分类
    ancient = {'jing': [], 'shi': [], 'zi': [], 'ji': []}
    modern_books = []
    journal_articles = []
    theses = []
    
    for info in all_citations:
        if info['type'] == 'ancient' or (info['dynasty'] and info['dynasty'] in DYNASTY_ORDER):
            category = classify_ancient(info.get('book', ''), info.get('original', ''))
            ancient[category].append(info)
        elif info['type'] == 'journal':
            journal_articles.append(info)
        elif info['type'] == 'thesis':
            theses.append(info)
        else:
            modern_books.append(info)
    
    # 去重并排序
    for cat in ancient:
        ancient[cat] = deduplicate_by_book(ancient[cat])
        ancient[cat].sort(key=dynasty_sort_key)
    
    modern_books = deduplicate_by_book(modern_books)
    modern_books.sort(key=lambda x: int(x.get('year', '9999')) if x.get('year', '').isdigit() else 9999)
    
    journal_articles = deduplicate_by_book(journal_articles)
    journal_articles.sort(key=lambda x: int(x.get('year', '9999')) if x.get('year', '').isdigit() else 9999)
    
    # 输出结果
    print("=" * 60)
    print("参考文献")
    print("=" * 60)
    
    print("\n一、古籍文献\n")
    
    cat_names = {'jing': '（一）经部', 'shi': '（二）史部', 'zi': '（三）子部', 'ji': '（四）集部'}
    for cat in ['jing', 'shi', 'zi', 'ji']:
        print(f"\n    {cat_names[cat]}\n")
        for i, info in enumerate(ancient[cat], 1):
            ref = format_reference_for_list(info)
            print(f"{i}. {ref}")
    
    print("\n\n二、今人专著\n")
    for i, info in enumerate(modern_books, 1):
        ref = format_reference_for_list(info)
        print(f"{i}. {ref}")
    
    print("\n\n三、期刊论文\n")
    for i, info in enumerate(journal_articles, 1):
        ref = format_reference_for_list(info)
        print(f"{i}. {ref}")
    
    if theses:
        print("\n\n四、学位论文\n")
        for i, info in enumerate(theses, 1):
            ref = format_reference_for_list(info)
            print(f"{i}. {ref}")
    
    return {
        'ancient': ancient,
        'modern_books': modern_books,
        'journal_articles': journal_articles,
        'theses': theses,
        'all_citations': all_citations,
        'skipped': skipped,
    }


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '郑璎_《汉唐百戏书写研究》二稿参考文献1_20260225.docx'
    result = process_all(path)
    
    print("\n\n" + "=" * 60)
    print("跳过的非引用脚注：")
    print("=" * 60)
    for fn_id, text in result['skipped']:
        print(f"  [{fn_id}] {text}")
