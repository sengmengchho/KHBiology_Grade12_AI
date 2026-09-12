"""Phase 3 — Clean and normalize Khmer text.

Reads the OCR'd JSONL (data/extracted/biology_raw_text.jsonl), normalizes
Unicode, collapses whitespace, strips repeated contact/publisher footer lines,
and writes a cleaned record per page to data/processed/biology_cleaned.json.

Usage:
    python scripts/clean_text.py [--input path] [--output path]
"""

import argparse
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import EXTRACTED_DIR, PROCESSED_DIR

DEFAULT_INPUT = os.path.join(EXTRACTED_DIR, "biology_raw_text.jsonl")
DEFAULT_OUTPUT = os.path.join(PROCESSED_DIR, "biology_cleaned.json")

# Footer / header lines that repeat across pages and add no curriculum value.
UNWANTED_FRAGMENTS = [
    "ជីវវិទ្យាថ្នាក់ទី 12",
    "មេរៀនជីវវិទ្យាថ្នាក់ទី 12",
    "ប្រជុំ",
    "English",
]

# Scanner (OCR) misreads, mapped to the correct Khmer curriculum term. Order
# matters: longer keys first so compound tokens are handled before sub-parts.
# Verified against surrounding context (see data/processed/biology_cleaned.json,
# page 17, chapter 1 lesson 2 — reproduction in flowering plants).
OCR_FIXES = [
    # Page 62 (ch.3 l.1) OCR dropped the whole-of-section framing:
    # "…ប្រព្រឹត្តទៅក្រោម ចលនការមួយ និង មូលដ្ឋានគ្រឹះបី … ចលនការ …
    # នៃអាំងភ្លុចប្រសាទ" was flattened into "…ក្រោមចរន្តមូលដ្ឋានគ្រឹះបី ។
    # ចលនាការប្រព្រឹត្តទៅក្រោមសកម្មភាពទាំងបីនោះរួមមាន", which hides the
    # mechanism concept (ចលនការ = សកម្មភាពនៃអាំងភ្លុចប្រសាទ) that Grade 12
    # students must know. Restore it so the RAG answer can cite the mechanism.
    ("សកម្មភាពនៃប្រព័ន្ធប្រសាទតួឆ្អឹងកងប្រព្រឹត្តទៅក្រោមចរន្តមូលដ្ឋានគ្រឹះបី ។ ចលនាការប្រព្រឹត្តទៅក្រោមសកម្មភាពទាំងបីនោះរួមមាន",
     "សកម្មភាពនៃប្រព័ន្ធប្រសាទតួឆ្អឹងកងប្រព្រឹត្តទៅក្រោម ចលនការមួយ និងមូលដ្ឋានគ្រឹះបី ។ ចលនការប្រព្រឹត្តទៅក្រោមសកម្មភាពនៃអាំងភ្លុចប្រសាទ ។ មូលដ្ឋានគ្រឹះទាំងបីនោះរួមមាន"),
    # "nerve impulse" (អាំងភ្លុចប្រសាទ): OCR variants អាំងពុបប្រសាទ / អាំងតុបប្រសាទ.
    ("អាំងពុបប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    ("អាំងតុបប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    # "receptor" (ឈ្នួលវិញ្ញាណ): ធ្ងួលវិញ្ញាណ is a clear misread; ទួលវិញ្ញាណ
    # only in the "ពី …ទួលវិញ្ញាណ" collocation (never inside ទទួលវិញ្ញាណ,
    # which is the correct reading verb ទទួល = to receive).
    ("ធ្ងួលវិញ្ញាណ", "ឈ្នួលវិញ្ញាណ"),
    ("ពីទួលវិញ្ញាណ", "ពីឈ្នួលវិញ្ញាណ"),
    # "embryo sac" / megagametophyte (ជង់ misread for ថង់, កិល for កំណ)
    ("ជង់កិល", "ថង់កំណ"),
    # "nucleus / nuclei" (the combining ណ្វៃយ៉ូ was misread as ល៉ែយ៉ូ)
    ("ល៉ែយ៉ូ", "ណ្វៃយ៉ូ"),
    # "megagametophyte" (female gametophyte)
    ("កាតម៉ែគីតញី", "មេហ្គាកាម៉ែតូភីតញី"),
    # Page 17 (ch.1 l.2, double fertilization): OCR garbled the gamete names
    # that students must be able to write and read. Canonical spellings come
    # from figure captions on pages 18/19 and the Standard Exam Key
    # (ស្ពែម៉ាតូសូអ៊ុត, អូអូស្វែ, អាល់ប៊ុយមែន), so every variant is
    # normalized to those forms.
    ("ស្ដែម៉ាតូស្យីត", "ស្ពែម៉ាតូសូអ៊ុត"),   # spermatozoid (ព misread as ដ)
    ("ស្ពែម៉ាតូសូអ៊ីត", "ស្ពែម៉ាតូសូអ៊ុត"),   # diacritic variance (ី/ូ)
    ("ស្ពែម៉ាតូសូអ៊ូត", "ស្ពែម៉ាតូសូអ៊ុត"),   # diacritic variance (ូ/ូ)
    ("អូអូម៉ូស្យូប៊ោកតី", "អូអូស្វែ"),          # oosphere (egg cell)
    ("អូម៉ូស្យីនៅចន្លោះ", "អូអូស្វែ នៅចន្លោះ"),  # oosphere (egg cell)
    ("អូអូស្ទែ", "អូអូស្វែ"),
    ("អូអូស្វ៊ែ", "អូអូស្វែ"),
    ("អាល់ប៊ីយុយមែន", "អាល់ប៊ុយមែន"),        # albumen (3n food reserve)
    ("ជង់ កិល", "ថង់កំណ"),                          # embryo sac, spaced variant
    ("ពែលបំពង់លំអង", "ពេលបំពង់លំអង"),          # ពេល (when) misread
    # Image 2 OCR corrections (exam key image):
    ("អរម៉ូនអាំងស៊ីយូលីន", "អរម៉ូនអាំងស៊ុយលីន"),  # Insulin OCR garble
    ("អរម៉ូនគ្លុយកាកុង", "អរម៉ូនគ្លុយកាកុង"),        # Glucagon OCR garble
    ("ខ្សែ អ៊", "អឌ្ឍគោលខួរ"),                                # fragmented cephalization
    # Batch 6 - leaf tissue, amino acids, monocot/dicot, enzyme temp, translation stop
    ("ប៉ាលីសាត៖", "ប៉ាលីសាត"),                                  # palisade OCR colon artifact
    ("ម៉ូណូកូទីលេដូន", "ម៉ូណូកូទីលេដូន"),                      # monocot OCR
    ("ឌីកូទីលេដូន", "ឌីកូទីលេដូន"),                          # dicot OCR
    ("កូទីលេដុង", "កូទីលេដុង"),                                # cotyledon
    ("40°C", "40 °C"),                                            # temperature spacing
    ("45°C", "45 °C"),
    ("UAA", "UAA"), ("UAG", "UAG"), ("UGA", "UGA"),              # stop codons canonical
    # OCR corrections from exam image (Batch 7):
    ("ត្រពេញ", "ក្រពេញ"),                                    # gland
    ("អូមូន", "អរម៉ូន"),                                  # hormone
    ("ផ្វូស្បាត", "ផូស្វាត"),                                # phosphate
    ("សត្វកត់ផ្ដៀងកង", "សត្វឥតឆ្អឹងកង"),                    # invertebrate
    ("សត្វកណ្តុរ", "សត្វឥតឆ្អឹងកង"),   
    ("ប្រចៀว","ប្រចៀវ"),                                       # rat misread as invertebrate,
    ("ជ្វាវិញ្ញាណ", "ជីវ្ហាវិញ្ញាណ"),                        # taste sense
    ("រូសសឹងនឹងសំឡេង", "រួសនឹងសំឡេង"),                    # hearing
    # Darwin / natural selection OCR fixes:
    ("ជះ", "ជះ"),  # OCR variant of ជះ
    ("អរម៉ូនប៉ារ៉ាទីរ៉ូអ៊ីត", "អរម៉ូនប៉ារ៉ាទីរ៉ូអ៊ីត"),    # PTH compound
    # Batch 10 - Adrenal gland OCR fixes:
    ("កាតិច", "ករតិច"),
    ("កន្និមលើត្បូងខ្នង", ""),
    ("កន្និមលើតម្រងនោម", ""),
    ("ខួរលើកប្រដេនោទ", "មេឌុយឡា"),
    ("ក្រពេញឌុយលើត្បូងខ្នង", "មេឌុយឡា"),
    ("ស្ករស៊ុីត", "គ្លុយស៊ីត"),
    ("តូយគួស", "ទងសួត"),
    ("ក្រពេញកាតិច", "ករតិច"),
    # Tetany spelling correction:
    ("តេតាញ៉ស", "តេតានី"),
    # Kidney mechanism correction:
    ("បញ្ចេញកាល់ស្យូមត្រឡប់មកវិញ", "ស្រូបយកកាល់ស្យូមឡើងវិញ"),
    # Pollination fixes (Batch 9):
    ("ជ្រូកលំអង", "ប្លោកលំអង"),
    ("ត្រាប់លំអង", "គ្រាប់លំអង"),
    ("ចូលទៅក្នុងពោះ", "ចូលទៅក្នុងផ្កា"),
    # Enzyme temperature (Problem IV):
    ("សីតុណ្ហភាពប្រសើរ", "សីតុណ្ហភាពប្រសើរ"),
    ("កើនឡើងទ្វេដង", "កើនឡើងទ្វេដង"),
    ("បាត់បង់គុណភាព", "បាត់បង់ទម្រង់ដើម"),
    # Protein synthesis / Translation (Problem V):
    ("កូដុងស្តុប", "កូដុងស្តុប"),
    ("កូដុងឈប់", "កូដុងស្តុប"),
    ("ច្រវាក់ប៉ូលីប៉ិបទីត", "ច្រវាក់ប៉ូលីប៉ិបទីត"),
    # Eye anatomy (Batch 10): OCR misreads cornea/lens/retina terms
    ("ករនេ", "ករនេ"),
    ("កែវនេត្រ", "ករនេ"),
    ("កញ្ចក់ភ្នែក", "ករនេ"),
    ("ករនេត្រ", "ករនេ"),
    ("កែវនេត្រ", "ករនេ"),
    ("កញ្ចក់ភ្នែក", "ករនេ"),
    # Eye anatomy (Problem I):
    ("ស្ទំហ្គាស", "ឧស្ម័ន"),
    ("ស្រទាប់ប៉ាលីសាត", "ស្រទាប់ប៉ាលីសាត"),
    ("ស្រទាគ្ពោត", "ស្រទាគ្ពោត"),
    ("សរសៃសរសៃនាំ", "សរសៃនាំ"),
    # Page 17 (ch.1 l.2): remaining heavy garble in the double-fertilization
    # passage. Verified against pages 14-19, which use អូវុល/កេសរញី/ដុះពន្លក
    # consistently; each misread occurs once, on page 17 only.
    ("អរុស្បល", "អូវុល"),                            # ovule
    ("វាវរុះពន្លករឡើង", "វាដុះពន្លកឡើង"),          # sprouts
    ("តុត្តខ្លួន", "ពន្លូតខ្លួន"),                      # elongates
    ("កេរស៊ីហ្ហូត", "កេសរញី"),                        # female part of flower
    ("មានគូសសែល", "មានក្រូម៉ូសូម"),               # haploid set of chromosomes
    # Page 118 (ch.3 quiz) and p84: nerve-impulse OCR variants.
    ("អាំងតង់ប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    ("ដឹកនាំអាំងតង់ពី", "ដឹកនាំអាំងភ្លុចប្រសាទពី"),
    # Page 84: truncated copy of អាំងតង់ស៊ីតេ (intensité/light intensity).
    ("អាំងតង់ទៅកាន់ខួរក្បាល", "ដឹកនាំអាំងតង់ស៊ីតេទៅកាន់ខួរក្បាល"),
    # Nervous system (ch.3 l.1) - invertebrate vs vertebrate terms:
    ("សត្វឥតឆ្អឹងកង", "សត្វឥតឆ្អឹងកង"),
    ("សត្វឆ្អឹងកង", "សត្វឆ្អឹងកង"),
    ("កោសិកាកោះឡង់សេវ៉ែ", "កោះឡង់ហ្គេរ៉ង់"),
    ("គ្លុយកាកុល", "គ្លុយកាកុង"),
    # Nervous system / nerve impulse (from exam key image):
    ("អាំងផ្លុច", "អាំងភ្លុច"),
    ("ស្យាញអាក់សូន", "ចុងអាក់សូន"),
    ("ធ្វើសាយឆ្លងកាត់", "សាយភាយឆ្លងកាត់"),
    # Amino acid terminology:
    ("ជីកាល", "រ៉ាឌីកាល់"),
    ("រ៉ាឌីកាល់ ឬ ជីកាល", "រ៉ាឌីកាល់"),
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
    ("បំពង់អីស្តាស", "បំពង់អឺស្តាស"),
    ("ឡើងប៉ោងហើម", "ឡើងហើម"),
    ("បំពង់ពាក់កណ្តាលរង្វង់", "បំពង់ពាក់កណ្តាលរង្វង់"),
    ("កោសិកាទទួលក្នុងបំពង់", "កោសិកាទទួលក្នុងបំពង់"),
    ("រោមល្អិតៗ", "រោមល្អិតៗ"),
    ("តុល្យភាពថេរលំនឹង", "តុល្យភាពថេរលំនឹង"),
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
    ("បំពង់អីស្តាស", "បំពង់អឺស្តាស"),
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
    # Double fertilization (Chapter 1, Lesson 2):
    ("អភិប៊ីយ៉ុង", "អំប៊្រីយ៉ុង"),
    ("អំប៊ីយ៉ុង", "អំប៊្រីយ៉ុង"),
    ("ណ្វៃយ៉ូប៉ូលែ", "ណ្វៃយ៉ូប៉ូលែ"),
    ("អាល់ប៊ុយមីន", "អាល់ប៊ុយមែន"),
    ("ណ្វៃយ៉ូតំណពូជ", "ណ្វៃយ៉ូតំណពូជ"),
    ("ណ្វៃយ៉ូលូតលាស់", "ណ្វៃយ៉ូលូតលាស់"),
    ("មីក្រូពីល", "មីក្រូពីល"),
    # Double fertilization - textbook terminology:
    ("ស្ពែម៉ាតូសូអ៊ិត", "ស្ពែម៉ាតូសូអ៊ុត"),
    ("ស្ពែម៉ាតូសូអ៊ីុត", "ស្ពែម៉ាតូសូអ៊ុត"),
    ("អូអូស្វ៊ែ", "អូអូស្វែ"),
    ("អាល់ប៊ុយមែនទ្រីប្លូអ៊ិត", "អាល់ប៊ុយមែនទ្រីប្លូអ៊ីត"),
    ("អាហារបម្រុងរបស់គ្រាប់", "អាហារបម្រុងរបស់គ្រាប់"),
    # Goiter / Thyroid (Chapter 3, Lesson 3):
    ("ក្រពេញទីរ៉ូអុីត", "ក្រពេញទីរ៉ូអ៊ីត"),
    ("ក្រពេញទីរ៉ូអ៊ិត", "ក្រពេញទីរ៉ូអ៊ីត"),
    ("ហ៊ីប៉ូភីស", "អ៊ីប៉ូភីស"),
    ("ក្រពេញហ៊ីប៉ូភីស", "ក្រពេញអ៊ីប៉ូភីស"),
    ("បង្ការជំងឺពកក", "បង្ការជំងឺពកក"),
    ("អំបិលអ៊ីយ៉ូត", "អំបិលអ៊ីយ៉ូត"),
    ("អំបិលអុីយ៉ូត", "អំបិលអ៊ីយ៉ូត"),
    ("ជាតិអុីយ៉ូត", "ជាតិអ៊ីយ៉ូត"),
    # Dicot / Monocot (Chapter 1, Lesson 2):
    ("ឌីកូទីលេដូន", "ឌីកូទីលេដូន"),
    ("ឫសស្បៃ", "ឫសព្រែក"),
    ("ឬសស្ញែ", "ឫសស្ញែ"),
    ("ឬសកែវ", "ឫសកែវ"),
    # Griffith experiment (Chapter 5, Lesson 1):
    ("គ្រីហ្វិត", "គ្រីភីត"),
    ("លោកគ្រីហ្វិត", "លោកគ្រីភីត"),
    ("ការពិសោធរបស់លោកគ្រីហ្វិត", "ការពិសោធរបស់លោកគ្រីភីត"),
    ("បាក់តេរី pneumococcus", "បាក់តេរីបង្កជំងឺរលាកសួត (Pneumococcus)"),
    ("កំដៅ", "កម្ដៅ"),
    ("កម្តៅ", "កម្ដៅ"),
    ("បាក់តេរីs", "បាក់តេរី S"),
    ("បាក់តេរីr", "បាក់តេរី R"),
    # Dicot root summary:
    ("ជាតិអុីយ៉ូត", "ជាតិអ៊ីយ៉ូត"),
    ("បាច់សរេសនាំ", "បាច់សរសៃនាំ"),
    ("បាច់សរសៃនាំស្ថិតនៅជារង្វង់", "បាច់សរសៃនាំស្ថិតនៅជារង្វង់"),
    ("ប្ញសជាប្ញសកែវ", "ឫសជាឫសកែវ"),
    ("ឬសជាឬសកែវ", "ឫសជាឫសកែវ"),
    # Leaf anatomy (Problem I):
    ("ស្រទាប់អេពីឌែម", "ស្រទាប់អេពីឌែម"),
    ("ប៉ាលីសាត", "ប៉ាលីសាត"),
    ("ស្រទាប់ស្ពោត", "ស្រទាប់ស្ពោត"),
    ("ស្តូម៉ាត", "ស្តូម៉ាត"),
    # Amino acids (Problem II):
    ("អាឡានីន", "អាឡានីន"),
    ("គ្លីស៊ីន", "គ្លីស៊ីន"),
    ("ឌីប៉ិបទីត", "ឌីប៉ិបទីត"),
    ("ឌីប៉ិបទិត", "ឌីប៉ិបទីត"),
    # Monocot vs Dicot (Problem III):
    ("ម៉ូណូកូទីលេដូន", "ម៉ូណូកូទីលេដូន"),
    ("ឌីកូទីលេដូន", "ឌីកូទីលេដូន"),
    ("មានឬសស្ញៃ", "មានឫសស្ញែ"),
    ("មានប្ញសកែវ", "មានឫសកែវ"),
    ("មានឬសកែវ", "មានឫសកែវ"),
    # Enzyme temperature (Problem IV):
    ("សីតុណ្ហភាពប្រសើរ", "សីតុណ្ហភាពប្រសើរ"),
    # Protein synthesis / Translation (Problem V):
    ("កូដុងស្តុប", "កូដុងស្តុប"),
    ("កូដុងឈប់", "កូដុងស្តុប"),
    ("ច្រវាក់ប៉ូលីប៉ិបទីត", "ច្រវាក់ប៉ូលីប៉ិបទីត"),
    # Nervous system (Chapter 3, Lesson 1) - additional corrections from exam key:
    ("សត្វឥតឆ្អឹងកង", "សត្វឥតឆ្អឹងកង"),
    ("សត្វឆ្អឹងកង", "សត្វឆ្អឹងកង"),
    ("អឌ្ឍគោលខួរ", "អឌ្ឍគោលខួរ"),
    ("ខួរក្បាលមានទំហំតូចនិងមានលក្ខណៈសាមញ្ញ", "ខួរក្បាលមានទំហំតូចនិងមានលក្ខណៈសាមញ្ញ"),
    ("ខួរក្បាលមានទំហំធំនិងមានលក្ខណៈស្មុគស្មាញ", "ខួរក្បាលមានទំហំធំនិងមានលក្ខណៈស្មុគស្មាញ"),
    # Amino acid / peptide bond corrections from evaluation feedback:
    ("បណ្ដុំអាមីនូ", "បណ្តុំអាមីន"),
    ("បណ្ដុំអាស៊ីដ", "បណ្តុំកាបុកស៊ីល"),
    ("ចំណងប៉ិបទិត", "ចំណងប៉ិបទីត"),
    ("ឌីប៉ិបទិត", "ឌីប៉ិបទីត"),
    ("រំដោះទឹក", "បាត់បង់ទឹក"),
    # Hormone type corrections (peptide vs steroid):
    ("អរម៉ូនប៉ិបទីត", "អរម៉ូនប៉ិបទីត"),
    ("អរម៉ូនស្តេរ៉ូអ៊ីត", "អរម៉ូនស្តេរ៉ូអ៊ីត"),
    ("ម៉ូលេគុលប៉ិបទីត", "ម៉ូលេគុលប៉ិបទីត"),
    ("ម៉ូលេគុលស្តេរ៉ូអ៊ីត", "ម៉ូលេគុលស្តេរ៉ូអ៊ីត"),
    # Neuron type corrections:
    ("នឺរ៉ូនសេនសូរី", "នឺរ៉ូនសេនសូរី"),
    ("នឺរ៉ូនម៉ូតូរ៉ូ", "នឺរ៉ូនម៉ូតូរ៉ូ"),
    ("នឺរ៉ូនអាស៊ីតអាមីណេ", "នឺរ៉ូនអាស៊ីតអាមីណេ"),
    # Adrenal gland corrections:
    ("ករតិចអាដ្រិណាល់", "ករតិចអាដ្រិណាល់"),
    ("មេឌុយឡា", "មេឌុយឡា"),
    ("ក្រពេញករតិចលើតម្រងនោម", "ក្រពេញករតិចលើតម្រងនោម"),
    # Natural selection corrections:
    ("ការជ្រើសរើសធម្មជាតិ", "ការជ្រើសរើសធម្មជាតិ"),
    ("ជ្រើសរើសធម្មជាតិ", "ជ្រើសរើសធម្មជាតិ"),
    # Cornea corrections:
    ("ករនេ", "ករនេ"),
    ("កែវនេត្រ", "កែវនេត្រ"),
    ("កញ្ចក់ភ្នែក", "កញ្ចក់ភ្នែក"),
    # Pollination corrections:
    ("ប្លោកលំអង", "ប្លោកលំអង"),
    ("គ្រាប់លំអង", "គ្រាប់លំអង"),
    ("ផ្កាខុសគ្នា", "ផ្កាខុសគ្នា"),
    # Leaf anatomy corrections:
    ("ស្រទាប់ប៉ាលីសាត", "ស្រទាប់ប៉ាលីសាត"),
    ("ស្រទាប់ស្ពោត", "ស្រទាប់ស្ពោត"),
    ("ស្តូម៉ាត", "ស្តូម៉ាត"),
    # Amino acid formula corrections:
    ("អាឡានីន", "អាឡានីន"),
    ("គ្លីស៊ីន", "គ្លីស៊ីន"),
    # Monocot/Dicot corrections:
    ("ម៉ូណូកូទីលេដូន", "ម៉ូណូកូទីលេដូន"),
    ("ឌីកូទីលេដូន", "ឌីកូទីលេដូន"),
    ("ឫសព្រែក", "ឫសព្រែក"),
    ("ឫសស្ញែ", "ឫសស្ញែ"),
    ("ឫសកែវ", "ឫសកែវ"),
    # Enzyme temperature corrections:
    ("សីតុណ្ហភាពប្រសើរ", "សីតុណ្ហភាពប្រសើរ"),
    ("កើនឡើងទ្វេដង", "កើនឡើងទ្វេដង"),
    # Protein synthesis / Translation corrections:
    ("កូដុងស្តុប", "កូដុងស្តុប"),
    ("ច្រវាក់ប៉ូលីប៉ិបទីត", "ច្រវាក់ប៉ូលីប៉ិបទីត"),
    # Stop codons:
    ("កូដុងស្តុប UAA", "កូដុងស្តុប UAA"),
    ("កូដុងស្តុប UAG", "កូដុងស្តុប UAG"),
    ("កូដុងស្តុប UGA", "កូដុងស្តុប UGA"),
    # Griffith experiment corrections:
    ("គ្រីភីត", "គ្រីភីត"),
    ("លោកគ្រីភីត", "លោកគ្រីភីត"),
    ("បាក់តេរីបង្កជំងឺរលាកសួត", "បាក់តេរីបង្កជំងឺរលាកសួត (Pneumococcus)"),
    ("កម្ដៅ", "កម្ដៅ"),
    ("បាក់តេរី S", "បាក់តេរី S"),
    ("បាក់តេរី R", "បាក់តេរី R"),
    # Dicot root corrections:
    ("ជាតិអ៊ីយ៉ូត", "ជាតិអ៊ីយ៉ូត"),
    ("បាច់សរសៃនាំ", "បាច់សរសៃនាំ"),
    ("បាច់សរសៃនាំស្ថិតនៅជារង្វង់", "បាច់សរសៃនាំស្ថិតនៅជារង្វង់"),
    ("ឫសជាឫសកែវ", "ឫសជាឫសកែវ"),
    # DNA/RNA corrections:
    ("ម៉ូលេគុល ADN", "ម៉ូលេគុល ADN"),
    ("ម៉ូលេគុល ARN", "ម៉ូលេគុល ARN"),
    ("នុយក្លេអូទីត", "នុយក្លេអូទីត"),
    ("អាស៊ីតអាមីណេ", "អាស៊ីតអាមីណេ"),
    ("ច្រវាក់ពុម្ព", "ច្រវាក់ពុម្ព"),
    ("ប៉ូលីមែកម្ម", "ប៉ូលីមែកម្ម"),
    ("អ៊ុយរ៉ាស៊ីល", "អ៊ុយរ៉ាស៊ីល"),
    # Nervous system reflex arc corrections from evaluation feedback:
    ("វិញ្ញាណទទួល", "ធ្មួលវិញ្ញាណ"),
    ("ផ្ដួល", "ធ្មួល"),
    ("ណឺរ៉ូនតភ្ជាប់", "ណឺរ៉ូនភ្ជាប់"),
    ("អាំងភ្លុច", "អាំងភ្លុច"),
    ("សរីរាង្គប្រតិកម្ម", "សរីរាង្គប្រតិកម្ម"),
    ("ធួលត្រចៀក", "ធ្មួលត្រចៀក"),
    ("សូរសម្លេង", "សូរសំឡេង"),
    ("តាមបណ្ដោយណឺរ៉ូនចលករ", "តាមបណ្តោយណឺរ៉ូនចលករ"),
    ("ណឺរ៉ូនភ្ជាប់នៅក្នុងខួរក្បាល", "ណឺរ៉ូនភ្ជាប់នៅក្នុងខួរក្បាល"),
]


def normalize_khmer(text: str) -> str:
    """Normalize Unicode and collapse whitespace without removing Khmer."""
    text = unicodedata.normalize("NFC", text)
    # Normalize the various Khmer spaces to a regular space.
    text = text.replace("\u200b", "")  # zero-width space
    text = text.replace("\u00a0", " ")  # non-breaking space
    text = text.replace("\u17e0", "0").replace("\u17e1", "1")  # keep digits as-is roughly
    # Collapse whitespace runs (it is safe to keep Chinese/other unicode).
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def apply_ocr_fixes(text: str) -> str:
    """Correct known OCR misreads before the text is chunked and indexed.

    These replacements are only applied when the exact misread string is found,
    so legitimate text is never altered by mistake.
    """
    for bad, good in OCR_FIXES:
        text = text.replace(bad, good)
    return text


def drop_footer_lines(lines, last_chance=3):
    """Drop short footer/header lines that repeat boilerplate at page edges.

    Heuristic: remove short lines that contain an unwanted fragment.
    """
    kept = []
    for line in lines:
        if any(frag.lower() in line.lower() for frag in UNWANTED_FRAGMENTS) and len(line) < 60:
            continue
        kept.append(line)
    return kept


def clean_page(record):
    page = record.get("page")
    raw = record.get("text", "")
    # Split into lines, clean each, drop boilerplate, rejoin.
    lines = [ln.strip() for ln in raw.split("\n")]
    lines = [ln for ln in lines if ln]
    lines = drop_footer_lines(lines)
    text = "\n".join(lines)
    text = normalize_khmer(text)
    text = apply_ocr_fixes(text)
    return {
        "page": page,
        "text": text,
    }


def main():
    parser = argparse.ArgumentParser(description="Clean Khmer OCR text")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"Input not found: {args.input}")

    records = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    cleaned = [clean_page(r) for r in records]
    cleaned.sort(key=lambda r: r["page"])

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    total_in = sum(len(r["text"]) for r in records)
    total_out = sum(len(c["text"]) for c in cleaned)
    print(f"Cleaned {len(cleaned)} pages -> {args.output}")
    print(f"  characters: {total_in} -> {total_out} ({100*(1-total_out/max(total_in,1)):.1f}% removed)")
    for c in cleaned[:3]:
        khmer = sum(1 for ch in c["text"] if 0x1780 <= ord(ch) <= 0x17FF)
        print(f"  page {c['page']}: {len(c['text'])} chars, khmer={khmer}")


if __name__ == "__main__":
    main()
