import json
import re

pages = {p['page']: p for p in json.load(open('data/processed/biology_cleaned.json', encoding='utf-8'))}
struct = json.load(open('data/processed/biology_structured.json', encoding='utf-8'))
meta = {p['page']: p for p in struct}
keys = ['ស្វ័យដំឡើង', 'ដំណើរទ្វេ', 'ស្ទិចម៉ាត', 'ស្អិត', 'លំអង',
        'ចំណងប៉ុបទីត', 'ចំណងប៉ិបទីត', 'ចំណងប៉បទីត', 'អាស៊ីតអាមីណេ',
        'បន្ស៊ាំ', 'បន្សំ', 'ជម្រើស', 'ARN', 'មហារីក', 'ហមារីក']
lines = []
for pno in (15, 16, 17, 122, 125, 126, 127, 130, 150, 157, 158, 159,
            164, 165, 174, 186, 202, 203, 236, 237):
    p = pages[pno]
    m = meta.get(pno, {})
    lines.append('=' * 80)
    lines.append(f"PAGE {pno} ch {m.get('chapter_id')} {m.get('chapter_title')} "
                 f"lesson {m.get('lesson_id')} {m.get('lesson_title')} len {len(p['text'])}")
    t = p['text']
    shown = set()
    for k in keys:
        for mt in re.finditer(re.escape(k), t):
            a = max(0, mt.start() - 120)
            b = min(len(t), mt.end() + 180)
            bucket = a // 100
            if bucket in shown:
                continue
            shown.add(bucket)
            lines.append(f'  [{k}] ...{t[a:b]}...')
            break
with open('_inspect_pages.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('wrote', len(lines), 'lines')
