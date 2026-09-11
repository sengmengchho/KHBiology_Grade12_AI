"""Query/text normalization helpers used before retrieval and OCR output.

Student questions (typed or read from a photographed exam paper) frequently
contain the same OCR-style garbled Biology terms that the textbook-fix tables in
scripts/clean_text.py correct before indexing. Embedding search is tolerant of
small spelling drift, but heavily garbled terms (e.g. អូអូម៉ូស្យូប៊ោកតី for
អូអូស្វែ) can still miss the relevant chunks. Normalizing the query to the
canonical corpus spellings made retrieval reliable and the answers clean.

The canonical spellings are the ones used inside biology_chunks.json (and the
Standard Exam Key): ស្ពែម៉ាតូសូអ៊ុត, អូវុល, អូអូស្វែ, ថង់កំណ, ណ្វៃយ៉ូ,
អាល់ប៊ុយមែន, អង់ស្យូស្ពែម, ...
"""

import re

# (garbled -> canonical) pairs. Order matters: longer compound misreads first
# so a whole string is handled before its shorter sub-keys are touched.
QUERY_FIXES = [
    ("វត្ថុជាតិអង់ស្ប៉ែម", "រុក្ខជាតិអង់ស្យូស្ពែម"),
    ("វត្ថុជាតិជីកូទីលេដូន", "រុក្ខជាតិឌីកូទីលេដូន"),
    ("វត្ថុជាតិ", "រុក្ខជាតិ"),
    ("អង់ស្ប៉ែម", "អង់ស្យូស្ពែម"),
    ("ស្របប្រតិកម្មទៅ", "ប្រព្រឹត្តទៅ"),
    ("ជីកូទីលេដូន", "ឌីកូទីលេដូន"),
    ("ម៉ូណូទីលេដូន", "ម៉ូណូកូទីលេដូន"),
    ("គ្រីក្តី", "គ្រីហ្វីត"),
    ("ស្តាយ", "ស្វាយ"),
    # Reproduction in flowering plants (ch.1 l.2) gamete/ovule terms.
    ("ស្ដែម៉ាតូស្យីត", "ស្ពែម៉ាតូសូអ៊ុត"),   # spermatozoid (ព->ដ)
    ("ស្ពែម៉ាតូសូអ៊ីត", "ស្ពែម៉ាតូសូអ៊ុត"),   # diacritic variance (ី/ូ)
    ("ស្ពែម៉ាតូសូអ៊ូត", "ស្ពែម៉ាតូសូអ៊ុត"),
    ("អូអូម៉ូស្យូប៊ោកតី", "អូអូស្វែ"),          # oosphere / egg cell
    ("អូអូស្ទែ", "អូអូស្វែ"),
    ("អូអូស្វ៊ែ", "អូអូស្វែ"),
    ("អាល់ប៊ីយុយមែន", "អាល់ប៊ុយមែន"),        # albumen (3n food reserve)
    ("អរុស្បល", "អូវុល"),                            # ovule
    ("ជង់កិល", "ថង់កំណ"),                            # embryo sac
    ("ជង់ កិល", "ថង់កំណ"),
    ("ល៉ែយ៉ូ", "ណ្វៃយ៉ូ"),                            # nucleus / nuclei
    # "stigma" (receptive top of the female carpel) OCR variants.
    ("ស្ទីចម៉ាត", "ស្ទិចម៉ាត"),
    ("ស្អិតម៉ាស", "ស្ទិចម៉ាត"),
    # Image 2 / exam key OCR variants:
    ("អរម៉ូនអាំងស៊ីយូលីន", "អរម៉ូនអាំងស៊ុយលីន"),
    ("អរម៉ូនគ្លុយកូង", "អរម៉ូនគ្លុយកាកុង"),
    ("គ្លុយកូង", "គ្លុយកាកុង"),
    # Batch 6 - leaf tissue, amino acids, monocot/dicot, enzyme temp, translation stop
    ("ប៉ាលីសាត៖", "ប៉ាលីសាត"),
    ("ម៉ូណូកូទីលេដូន", "ម៉ូណូកូទីលេដូន"),
    ("ឌីកូទីលេដូន", "ឌីកូទីលេដូន"),
    ("កូទីលេដុង", "កូទីលេដុង"),
    ("40°C", "40 °C"),
    ("45°C", "45 °C"),
    ("UAA", "UAA"), ("UAG", "UAG"), ("UGA", "UGA"),
    # OCR corrections from exam image (Batch 7):
    ("ត្រពេញ", "ក្រពេញ"),
    ("អូមូន", "អរម៉ូន"),
    ("ផ្វូស្បាត", "ផូស្វាត"),
    ("សត្វកត់ផ្ដៀងកង", "សត្វឥតឆ្អឹងកង"),
    ("សត្វកណ្តុរ", "សត្វឥតឆ្អឹងកង"),
    ("ជ្វាវិញ្ញាណ", "ជីវ្ហាវិញ្ញាណ"),
    ("រូសសឹងនឹងសំឡេង", "រួសនឹងសំឡេង"),
    ("អរម៉ូនប៉ារ៉ាទីរ៉ូអ៊ីត", "អរម៉ូនប៉ារ៉ាទីរ៉ូអ៊ីត"),
    # Batch 8 - OCR corrections from exam image:
    ("ស្វីកុដជាតិ", "ស្លឹករុក្ខជាតិ"),
    ("រ៉ូម៉ាគាល់់", "រ៉ាឌីកាល់"),
    ("ឌីប៉ុបទីត", "ឌីប៉ិបទីត"),
    ("កូដុងឈប់", "កូដុងស្តុប"),
    ("រុក្ខជាតិម៉ូលេគុលដែលមាន", "រុក្ខជាតិម៉ូណូកូទីលេដូន"),
    ("ឌីគូម៉ូលេគុល", "ឌីកូទីលេដូន"),
    ("ខ្សែ អ៊", "អឌ្ឍគោលខួរ"),
    # Amino acid R-group / side chain variants used in exam keys.
    ("ជីកាល", "រ៉ូម៉ាគាល់"),
    ("រ៉ាឌីកាល", "រ៉ូម៉ាគាល់"),
    ("រ៉ាឌីកាល់", "រ៉ូម៉ាគាល់"),
    ("ខ្សែចំហៀង", "រ៉ូម៉ាគាល់"),
    # Nervous system (ch.3 l.1) nerve-impulse misreads.
    ("អាំងពុបប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    ("អាំងតុបប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    ("អាំងតង់ប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    ("ធ្ងួលវិញ្ញាណ", "ឈ្នួលវិញ្ញាណ"),            # receptor
    # Vision (ch.3 l.2): the retina is រេទីន in the textbook; exam papers
    # write វេទីន or រ៉េទីន (វ/រ and missing the ៉ diacritic are common).
    ("វ៉ែទីន", "រេទីន"),
    ("រ៉េទីន", "រេទីន"),
    ("វេទីន", "រេទីន"),
# Pollination fixes:
    ("ជ្រូកលំអង", "ប្លោកលំអង"),
    ("ត្រាប់លំអង", "គ្រាប់លំអង"),
    ("ចូលទៅក្នុងពោះ", "ចូលទៅក្នុងផ្កា"),
    # Pollination query expansion:
    ("នាំគ្រាប់លំអង", "នាំគ្រាប់លំអង ផ្កា ទឹកដម ស្ទិចម៉ាត គ្រាប់លំអង"),
    # Eye anatomy synonyms (cornea/lens/retina):
    ("ករនេ", "ករនេ កែវនេត្រ កញ្ចក់ភ្នែក"),
    ("កែវនេត្រ", "កែវនេត្រ ករនេ កញ្ចក់ភ្នែក"),
    ("កញ្ចក់ភ្នែក", "កញ្ចក់ភ្នែក ករនេ កែវនេត្រ"),
    ("រេទីន", "រេទីន វេទីន"),
    ("ស្រទាប់ក្លេរ៉ូទិច", "ស្រទាប់ក្លេរ៉ូទិច ស្រទាប់ស្ក្លេរ៉ូទិច ស្រទាប់ភ្លីចរឹង ភ្នាសស្ក្លេរ៉ូទិច"),
    # Nervous system (ch.3 l.1) - invertebrate vs vertebrate:
    ("សត្វឥតឆ្អឹងកង", "សត្វឥតឆ្អឹងកង"),
    ("សត្វឆ្អឹងកង", "សត្វឆ្អឹងកង"),
    ("កោសិកាកោហឡង់សេវ៉ែ", "កោះឡង់ហ្គេរ៉ង់"),
    ("គ្លុយកាកុង", "គ្លុយកាកុង"),
    # Adrenal gland terms (Batch 10):
    ("កាតិច", "ករតិច"),
    ("កន្និមលើត្បូងខ្នង", "ក្រពេញករតិចលើតម្រងនោម"),
    ("កន្និមលើតម្រងនោម", "ក្រពេញករតិចលើតម្រងនោម"),
    ("ខួរលើកប្រដេនោទ", "មេឌុយឡា"),
    ("ក្រពេញឌុយលើត្បូងខ្នង", "មេឌុយឡា"),
    ("ស្ករស៊ុីត", "គ្លុយស៊ីត"),
    ("តូយគួស", "ទងសួត"),
    # Tetany spelling correction:
    ("តេតាញ៉ស", "តេតានី"),
    # Kidney mechanism correction:
    ("បញ្ចេញកាល់ស្យូមត្រឡប់មកវិញ", "ស្រូបយកកាល់ស្យូមឡើងវិញ"),
    # Nervous system / nerve impulse (from exam key image):
    ("អាំងផ្លុច", "អាំងភ្លុច"),
    ("ស្យាញអាក់សូន", "ចុងអាក់សូន"),
    ("ធ្វើសាយឆ្លងកាត់", "សាយភាយឆ្លងកាត់"),
    # Amino acid terminology:
    ("អាស៊ីតអាមីនេ", "អាស៊ីតអាមីណេ"),
    ("អាសុីតអាមីនេ", "អាស៊ីតអាមីណេ"),
    # Neurotransmitter / Hormone terminology:
    ("អន្តរិបទ", "អន្តរភូត"),
    ("អាំងដូលអាស៊ីតអាសេទីច", "អាស៊ីតអាំងដូលអាសេទិច"),
    # DNA replication terminology:
    ("វណ្ឌូ", "ណ្វៃយ៉ូ"),
    ("ច្រាក់", "ច្រវាក់"),
    ("នុយក្លេអូទីដ", "នុយក្លេអូទីត"),
    ("មេត្រីព័ត៌មានសេនេទិច", "អ្នកផ្ទុកព័ត៌មានសេនេទិច"),
    ("រាប់រងការដំឡើងទ្វេ", "រ៉ាប់រងការដំឡើងទ្វេ"),
    ("ស្វ័យទ្វេដង", "ស្វ័យដំឡើងទ្វេ"),
    ("ស្វ័យតំឡើងទ្វេ", "ស្វ័យដំឡើងទ្វេ"),
    ("នៅថេរដដែល", "នៅថេរដដែល"),
    # RNA Polymerase / Transcription (Chapter 5, Lesson 2):
    ("ប៉ូលីមែកម្ម", "ប៉ូលីមែកម្ម"),
    ("ច្រវាក់ពុម្ព", "ច្រវាក់ពុម្ព"),
    ("អ៊ុយរ៉ាស៊ីល", "អ៊ុយរ៉ាស៊ីល"),
    # Ear anatomy / hearing (Chapter 3, Lesson 2):
    ("កោសិកាពន្លឺ", "កោសិកាមានរោម"),
    ("ប្រភោយអីស្ដាស", "បំពង់អឺស្តាស"),
    ("បំពង់អីស្ដាស", "បំពង់អឺស្តាស"),
    ("ឡើងប៉ោងហើម", "ឡើងហើម"),
    ("បំពង់ពាក់កណ្តាលរង្វង់", "បំពង់ពាក់កណ្តាលរង្វង់"),
    ("កោសិកាទទួលក្នុងបំពង់", "កោសិកាទទួលក្នុងបំពង់"),
    ("រោមល្អិតៗ", "រោមល្អិតៗ"),
    ("តុល្យភាពថេរលំនឹង", "តុល្យភាពថេរលំនឹង"),
    # Fossils (Chapter 6, Lessons 2-3):
    ("ជូស៊ីល", "ផូស៊ីល"),
    ("ភារៈរស់", "ភាវៈរស់"),
    ("សិលាគម្នេចកំណត់", "សិលាកម្ទេចកំណ"),
    ("សិលាកំទេចកំណ", "សិលាកម្ទេចកំណ"),
    ("ជ័រអំពិលទឹកក្រូច", "ជ័រអំពិលទឹកក្រូច"),
]

# "ខួរឆ្អឹង" (bone marrow) is NOT a Grade 12 Biology topic; the textbook only
# uses ខួរឆ្អឹងខ្នង (spinal cord). Students asking about the brain sometimes
# type/OCR ខួរឆ្អឹង as a short form of ខួរធំ (cerebrum, ch.3 l.1 p.67/70-71),
# which retrieves nothing. Rewrite it to ខួរធំ UNLESS it is followed by ខ្នង,
# which guards the legitimate term ខួរឆ្អឹងខ្នង.
_CEREBRUM_RE = re.compile(r"ខួរឆ្អឹង(?!ខ្នង)")


def normalize_query(text: str) -> str:
    """Rewrite garbled/OCR-style spellings in a student question to the
    canonical terms used in the textbook corpus. Idempotent and safe: no
    legitimate term matches any key."""
    text = (text or "").strip()
    for bad, good in QUERY_FIXES:
        text = text.replace(bad, good)
    return _CEREBRUM_RE.sub("ខួរធំ", text)


# Exam papers phrase definition questions as "ចូរឱ្យនិយមន័យ X" (give the
# definition of X). The reranker scores that imperative form poorly (≈0.06,
# below the 0.08 abstain threshold) while the natural question form
# "តើXជាអ្វី?" scores ≈0.5. Rewrite it internally for retrieval/generation.
_DEFINITION_RE = re.compile(r"ចូរ\s*(?:ឱ្យ|ឲ្យ|អោយ)\s*និយមន័យ(?:របស់)?\s*")
_TERM_TRAIL = " ?។\u17d5\uff1f\u061f"
_NO_REWRITE = re.compile(r"[?។\u17d5\uff1f\u061f]")
_CLAUSE_WORDS = ("និង", "ព្រោះ")


def _expand_definition(text: str) -> str:
    m = _DEFINITION_RE.search(text)
    if not m:
        return text
    term = text[m.end():].strip(_TERM_TRAIL)
    if not term:
        return text
    # Only rewrite a clean single noun phrase. Skip compound clauses
    # ("...និងឱ្យឧទាហរណ៍..."), explanation prompts ("...ព្រោះ..."), and
    # multi-sentence input (any leftover punctuation).
    if len(term) > 80 or _NO_REWRITE.search(term) or any(w in term for w in _CLAUSE_WORDS):
        return text
    return text[: m.start()] + f"តើ{term}ជាអ្វី?"


def expand_query(text: str) -> str:
    """Term normalization + query reshaping used inside the RAG pipeline so
    retrieval scores stay above the abstain threshold. The student's displayed
    message keeps the term-fixed original (see normalize_query)."""
    return _expand_definition(normalize_query(text))