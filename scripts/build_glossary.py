"""Build a Biology glossary from the processed textbook chunks.

Extracts "term + definition" pairs from the Khmer text by scanning for
definition markers (គឺជា / គឺ / ជា / មានន័យថា / ហៅថា). Records an English
gloss when a Latin term appears in parentheses. No LLM calls are used.

Outputs:
    data/glossary/glossary.json   (structued entries)
    data/glossary/glossary.md     (human-readable reference)

Usage:
    python scripts/build_glossary.py
"""

import json
import os
import re

DATA_DIR = os.path.join('data', 'processed', 'biology_chunks.json')
OUT_DIR = os.path.join('data', 'glossary')
OUT_JSON = os.path.join(OUT_DIR, 'glossary.json')
OUT_MD = os.path.join(OUT_DIR, 'glossary.md')

# Khmer definition markers (longest first so regex prefers the full phrase).
MARKERS = ['គឺជាប់', 'គឺជា', 'មានន័យថា', 'គឺ', 'ជា', 'ហៅថា']

# Khmer letters live in U+1780..U+17FF.
KM = r'\u1780-\u17FF'
# A word must START on a consonant/independent vowel (U+1780..U+17AB).
# Khmer has no word separators, so most bio terms are a single contiguous
# run (e.g. ស្តូម៉ាត, អង់ដូស្ពែម). Cap the length; longer is a clause.
KM_START = r'\u1780-\u17AB'
KM_BODY = r'\u1780-\u17FF\u200c\u200d'
WORD = rf'[{KM_START}][{KM_BODY}]{{1,18}}'
# A glossary term is a single contiguous Khmer run.
TERM1 = rf'({WORD})'
# Word must not be preceded by another Khmer char (avoids capturing suffixes).
WORD_BD = rf'(?<![{KM_BODY}])'

# Clause particles that appear inside Khmer words/phrases; if one of these
# appears bare inside the term it is likely a phrase, not a term.
TERM_BAD_CHARS = ('.', '។', '៖', ':', '$', '/', '\\', '[', ']')

# Pattern 1: "long description ហៅថា TERM"  -> term is on the RIGHT of marker.
CALLED_RE = re.compile(
    rf'(?P<def>[^។\n\r]{{10,220}}?)\s*ហៅថា\s*\**\s*{WORD_BD}'
    rf'(?P<term>{WORD})'
    rf'\s*\**\s*(?=[\)\s,;)។]|$)'
)

# Pattern 2: "TERM គឺជា definition" or "TERM គឺ definition" -> term on LEFT.
IS_RE = re.compile(
    rf'{WORD_BD}(?P<term>{WORD})\s*(គឺជា|គឺ)\s+'
    rf'(?P<def>[^។\n\r]{{5,220}}?)'
)

# English gloss in parentheses, e.g. "កោសិកា (cell)" or "(deoxyribonucleic acid)".
LATIN_RE = re.compile(r'\(([A-Za-z][A-Za-z0-9 ,./-]{1,60}?)\)')

# Terms that are unlikely to be glossary-worthy.
BAD_START = (
    'ដើម្បី', 'ព្រោះ', 'អាច', 'ការ', 'ដោយ', 'ដែល', 'ហើយ',
    'បន្ទាប់', 'មុន', 'ក្រោយ', 'នៅ', 'ទៅ', 'មក', 'ចំពោះ',
    'ដោយសារ', 'នៅពេល', 'ពីព្រោះ', 'រួមទាំង',
)
BAD_DEF_START = (
    'ដូចម្តេច', 'ដូចម្ដេច', '?', 'ចូរ', 'តើ',
    '\u0024\\squ', '❓', '។', 'ឃ.', 'គ.', 'ខ.', 'ក.', '(', 'ក. ',
    ')', 'លំហាត់', 'សំណួរ',
)
BAD_WORDS = ('តើ', '?', 'សំណួរនិងលំហាត់', '។')


def clean_term(t, raw_group):
    t = re.sub(r'\*+', '', t).strip().strip(' "-')
    t = re.sub(r'\s+', ' ', t).strip('[:?().;»«')
    for w in BAD_START:
        if t.startswith(w):
            return None
    if any(ch in t for ch in TERM_BAD_CHARS):
        return None
    if any(w in t for w in BAD_WORDS):
        return None
    if len(t) < 2 or len(t) > 20:
        return None
    # Term must contain at least one Khmer letter.
    if not re.search(('[%s]' % KM), t):
        return None
    # Keep that we also need the term present in the ORIGINAL matched text
    # (guards against off-by-N captures).
    if t not in raw_group:
        return None
    return t


def clean_def(d):
    d = re.sub(r'\*+', '', d)
    d = re.sub(r'\s+', ' ', d)
    d = d.lstrip(' •·-–—:«»“”"\' \t').strip()
    d = re.sub(r'\s+', ' ', d)
    if len(d) < 8:
        return None
    for p in BAD_DEF_START:
        if d.startswith(p):
            return None
    # Reject definitions that are actually multiple-choice options.
    if re.match(r'^[a-zA-Zក-អ]\s*[.):]', d):
        return None
    return d


def main():
    with open(DATA_DIR, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    entries = []
    for c in chunks:
        text = c['text'].replace('\u00a0', ' ')

        for m in CALLED_RE.finditer(text):
            term = clean_term(m.group('term'), m.group(0))
            definition = clean_def(m.group('def'))
            if term is None or definition is None:
                continue
            if 'ហៅថា' in definition:
                continue
            latin = re.search(LATIN_RE, m.group(0))
            entries.append({
                'term': term, 'definition': definition, 'marker': 'ហៅថា',
                'en': latin.group(1).strip() if latin else '',
                'page': c.get('page'), 'chapter_id': c.get('chapter_id'),
                'chapter_title': c.get('chapter_title'),
                'lesson_id': c.get('lesson_id'),
                'lesson_title': c.get('lesson_title'),
            })

        for m in IS_RE.finditer(text):
            term = clean_term(m.group('term'), m.group(0))
            definition = clean_def(m.group('def'))
            if term is None or definition is None:
                continue
            latin = re.search(LATIN_RE, m.group(0))
            entries.append({
                'term': term, 'definition': definition, 'marker': m.group(2),
                'en': latin.group(1).strip() if latin else '',
                'page': c.get('page'), 'chapter_id': c.get('chapter_id'),
                'chapter_title': c.get('chapter_title'),
                'lesson_id': c.get('lesson_id'),
                'lesson_title': c.get('lesson_title'),
            })

    # Deduplicate by term; prefer entries with an English gloss, else longest definition.
    by_term = {}
    for e in entries:
        key = e['term'].strip()
        # Canonical key ignores spaces so "កង់គ្លី យ៉ុង" merges with "កង់គ្លីយ៉ុង".
        canon = key.replace(' ', '')
        if canon not in by_term:
            e['sources'] = []
            by_term[canon] = e
        else:
            prev = by_term[canon]
            prefer = (e.get('en') and not prev.get('en'))
            longer = len(e['definition']) > len(prev['definition'])
            if prefer or longer:
                by_term[canon] = e
                e['sources'] = prev.get('sources', [])
            if e.get('page') and e['page'] not in prev.get('sources', []):
                prev.setdefault('sources', []).append(e['page'])

    final = sorted(by_term.values(), key=lambda e: e['term'])
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    # Markdown reference, grouped by chapter.
    lines = ['# វចនានុក្រមជីវវិទ្យា (Biology Glossary)', '',
             f'ពាក្យសរុប: {len(final)}', '']
    by_ch = {}
    for e in final:
        by_ch.setdefault(e.get('chapter_id', 0), []).append(e)
    for ch in sorted(by_ch):
        if ch == 0:
            continue
        title = by_ch[ch][0].get('chapter_title') or ch
        lines.append(f'## ជំពូក {ch}: {title}')
        for e in by_ch[ch]:
            en = f' ({e["en"]})' if e.get('en') else ''
            page = f' (ទំព័រ {e["page"]})' if e.get('page') else ''
            lines.append(f'- **{e["term"]}**{en} — {e["definition"]}{page}')
        lines.append('')
    extra = by_ch.get(0, [])
    if extra:
        lines.append('## ផ្សេងៗ')
        for e in extra:
            en = f' ({e["en"]})' if e.get('en') else ''
            page = f' (ទំព័រ {e["page"]})' if e.get('page') else ''
            lines.append(f'- **{e["term"]}**{en} — {e["definition"]}{page}')

    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'extracted {len(entries)} raw matches -> {len(final)} unique terms')
    print(f'saved {OUT_JSON}')
    print(f'saved {OUT_MD}')


if __name__ == '__main__':
    main()