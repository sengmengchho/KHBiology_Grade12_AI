"""Query/text normalization helpers used before retrieval and OCR output.

Student questions (typed or read from a photographed exam paper) frequently
contain the same OCR-style garbled Biology terms that the textbook-fix tables in
scripts/pipeline/clean_text.py correct before indexing. Embedding search is tolerant of
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
    # "gene": exam papers/students write ហ្សែន; the textbook corpus uses សែន.
    ("ហ្សែន", "សែន"),
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
    ("ស្រទាប់ស្ពោត", "ស្រទាគ្ពោត"),
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
    ("ណឺរ៉ូនតភ្ជាគ់", "ណឺរ៉ូនភ្ជាគ់"),
    ("អាំងភ្លុច", "អាំងភ្លុច"),
    ("សរីរាង្គប្រតិកម្ម", "សរីរាង្គប្រតិកម្ម"),
    ("ធួលត្រចៀក", "ធ្មួលត្រចៀក"),
    ("សូរសម្លេង", "សូរសំឡេង"),
    ("តាមបណ្ដោយណឺរ៉ូនចលករ", "តាមបណ្តោយណឺរ៉ូនចលករ"),
    ("ណឺរ៉ូនភ្ជាគ់នៅក្នុងខួរក្បាល", "ណឺរ៉ូនភ្ជាគ់នៅក្នុងខួរក្បាល"),
    # Protein comparison (Chapter 4, Lesson 2) - Globular vs Fibrous:
    ("ប្រូតេអ៊ីនគ្រាប់", "ប្រូតេអ៊ីនគ្រាប់"),
    ("ប្រូតេអ៊ីនសរសៃ", "ប្រូតេអ៊ីនសរសៃ"),
    ("អាល់ប៊ុយមីន", "អាល់ប៊ុយមីន"),
    ("អេម៉ូក្លូប៊ីន", "អេម៉ូក្លូប៊ីន"),
    ("រាងស៊ែ", "រាងស៊្វែ"),
    ("កេរ៉ាទីន", "កេរ៉ាទីន"),
    ("កូឡាជែន", "កូឡាជែន"),
    ("ប៉ូលីប៉េបទីត", "ប៉ូលីប៉ិបទីត"),
    ("មិនរលាយក្នុងទឹក ស្វិត", "មិនរលាយក្នុងទឹក ស្វិត"),
    # Vision / Eye (Chapter 3, Lesson 2) - from evaluation feedback:
    ("កនេ", "កញ្ចក់ភ្នែក"),
    ("ក័រនេ", "កញ្ចក់ភ្នែក"),
    ("អាំងតង់ស៊ីតេប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    ("សរសៃប្រសាទអុបទិច", "សរសៃប្រសាទអុបទិក"),
    ("រន្ធប្រស្រីរួតតូច", "រន្ធប្រស្រីរួមតូច"),
    ("កោសិការ៉ូត", "កោសិការ៉ូដ"),
    ("កោសិកាទេ្វបូឡា", "កោសិកាទ្វេបូឡា"),
    ("កោសិកាកង់គ្លីយ៉ុង", "កោសិកាកង់គ្លីយ៉ុង"),
("ជាតិពណ៌រ៉ូដុបស៊ីន", "ជាតិពណ៌រ៉ូដុបស៊ីន"),
    ("ស្រឡាយជីវជាតិ A", "ស្រឡាយជីវជាតិ A"),
    ("សរសៃប្រសាទអុបទិច", "សរសៃប្រសាទអុបទិក"),
    # Fossil formation (Chapter 6, Lesson 3) - Mold/Cast fossils:
    ("ការរកើតនៃពុម្ពក្រៅ", "ការកកើតនៃពុម្ពក្រៅ"),
    ("សិប្បសត្វ", "សិប្បីសត្វ"),
    ("ពុម្ភក្រៅ", "ពុម្ពក្រៅ"),
    ("ពុម្ភក្នុង", "ពុម្ពក្នុង"),
    ("ចំណុចចុចទី៤", "ចំណុចទី ៤"),
    ("កម្ទេចកំនក", "កម្ទេចកំណក"),
    ("កំទេចកំណក", "កម្ទេចកំណក"),
    ("សាកសពរលួយបន្សល់ទុក", "សាកសពរលួយបន្សល់ទុក"),
    # Pancreas / Insulin / Glucagon (Chapter 3, Lesson 3) - from evaluation feedback:
    ("កោះអ៊ីឡូឡង់សេវ៉ែ", "អ៊ីឡូឡង់សេរ៉ង់"),
    ("អ៊ីឡូឡង់សេវ៉ែ", "អ៊ីឡូឡង់សេរ៉ង់"),
    ("កោសិកាបេតា", "កោសិកាបេតា"),
    ("កោសិកាអាល់ហ្វា", "កោសិកាអាល់ហ្វា"),
    ("គ្លីកូសទៅជាគ្លុយកូស", "គ្លីកូសែនទៅជាគ្លុយកូស"),
    ("កោសិកាពីររបប", "កោសិកាពីរប្រភេទ"),
    ("អ័រម៉ូនអាំងស៊ុយលីន", "អរម៉ូនអាំងស៊ុយលីន"),
    ("អ័រម៉ូនគ្លុយកាកុង", "អរម៉ូនគ្លុយកាកុង"),
    ("ក្រិតកំណត់", "កម្រិតកំណត់"),
    ("ប្លែងជាខ្លាញ់", "បំប្លែងជាខ្លាញ់"),
    ("ប្លែងទៅជាគ្លុយកូសវិញ", "បំប្លែងទៅជាគ្លុយកូសវិញ"),
    # Reflex arc - phone ringing (Chapter 3, Lesson 1) - additional from evaluation:
    ("សូររោទ៍", "សូរសំឡេងរោទ៍"),
    # Flower parts (Chapter 1, Lesson 2) - additional from evaluation:
    ("កញុំកេសញី", "កញ្ចុំកេសរញី"),
    ("កញុំកេសឈ្មោល", "កញ្ចុំកេសរឈ្មោល"),
    ("កញ្ចុំកេសញី", "កញ្ចុំកេសរញី"),
    ("កញ្ចុំកេសឈ្មោល", "កញ្ចុំកេសរឈ្មោល"),
    ("ផ្នែកផ្សេងៗរបស់ផ្កាមាន", "ផ្នែកផ្សេងៗរបស់ផ្កាមាន"),
    # Angiosperm classification (Chapter 1, Lesson 2):
    ("អង់ស្យូស្ពែមក", "អង់ស្យូស្ពែម"),
    ("កូទីលេដូនមួយនៅក្នុងគ្រាប់", "កូទីលេដុងមួយនៅក្នុងគ្រាប់"),
    # Dicot root / root tip (Chapter 1, Lesson 2):
    ("ដើមស្វាយជារុក្ខជាតិឌីកូទីលេដូន", "ដើមស្វាយជារុក្ខជាតិឌីកូទីលេដូន"),
    ("កូទីលេដុង ២", "កូទីលេដុង ២"),
    ("ទ្រនុងបែកខ្នែង", "ទ្រនុងបែកខ្នែង"),
    ("ឬសជាឬសកែវ", "ឬសជាឬសកែវ"),
    # Neuron classification (Chapter 3, Lesson 1):
    ("ឯកប្ដួល", "ឯកបូឡា"),
    ("ឯកប៉ូល", "ឯកបូឡា"),
    ("ទ្វេប្ដួល", "ទ្វេបូឡា"),
    ("ទ្វេប៉ូល", "ទ្វេបូឡា"),
    ("ពហុប្ដួល", "ពហុបូឡា"),
    ("ពហុប៉ូល", "ពហុបូឡា"),
    ("ឈ្នួលវិញ្ញាណ", "ធ្មួលវិញ្ញាណ"),
    ("ភាពពន្លាយស៊ីតូប្លាស", "ភាពពន្លយស៊ីតូប្លាស"),
    # Pituitary gland (Chapter 3, Lesson 3):
    ("ផូស៊ីលួរ", "អ៊ីប៉ូភីសមុខ"),
    ("មេឡាញ៉ូស៊ីត ស៊ីមុយឡង់", "មេឡាណូស៊ីតស្ទីមូយឡង់"),
    ("ទីរ៉េយ៉ូស្ទីមុយលីន", "ទីរ៉េអូស្ទីមូយលីន"),
    ("អាដ្រេណូកទីកូត្រូប", "អាដ្រេណូក័រទីកូត្រុប"),
    ("អង់ទីឌីអុយរេទីច", "អង់ទីឌីអ៊ុយរេទិច"),
    ("អរម៉ូនកូណាដូស្ទីមុយលីន", "អរម៉ូនកូណាដូស្ទីមូយលីន"),
    # Ear / Cochlea (Chapter 3, Lesson 2):
    ("បំពង់រាងគូទខ្យង", "បំពង់រាងកងធ្នូទងខ្យល់"),
    ("បំពង់រាងគូខ្យង", "បំពង់រាងកងធ្នូទងខ្យល់"),
    ("អាំងពុលស៊ីប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    ("អាំងភូប្រសាទ", "អាំងភ្លុចប្រសាទ"),
    # NB: no ("រលកសូ", "រលកសូរ") pair — plain replace() would corrupt the
    # already-correct "រលកសូរ" into "រលកសូររ". Guarded below.
    ("សរីរាង្គលឺ", "សរីរាង្គឮ"),
    # Tripeptide / Peptide bond (Chapter 4, Lesson 1):
    ("ទ្រីប៉ិបទិត", "ទ្រីប៉ិបទីត"),
    ("ទ្រីប៉េបទីត", "ទ្រីប៉ិបទីត"),
    ("ក្រុមកាបុកស៊ីល", "បណ្តុំកាបុកស៊ីល"),
    ("ក្រុមអាមីន", "បណ្តុំអាមីន"),
    ("ក្រុមអុីដ្រុកស៊ីល", "បណ្តុំអ៊ីដ្រុកស៊ីល"),
    # DNA vs RNA (Chapter 5, Lesson 2):
    ("ស្ករដេអុកស៊ីរីបូស", "ស្ករដេអុកស៊ីរីបូស"),
    ("ស្កររីបូស", "ស្កររីបូស"),
    ("បាសអុយរ៉ាស៊ីល", "បាសអ៊ុយរ៉ាស៊ីល"),
    ("បាសទីមីន", "បាសទីមីន"),
    ("អាស៊ីតនុយក្លេអ៊ិច", "អាស៊ីតនុយក្លេអ៊ិច"),
    # Stigma (Chapter 1, Lesson 2):
    ("ស្ទិចម៉ាតគឺជាផ្កំពូល", "ស្ទិចម៉ាតគឺជាផ្នែកកំពូល"),
    ("ស្ទិចម៉ាតជាផ្នែកកំពូល", "ស្ទិចម៉ាត គឺជាផ្នែកកំពូល"),
    ("ការពារកុំឱ្យគ្រាប់លំអងជ្រុះ", "ការពារកុំឱ្យគ្រាប់លំអងជ្រុះ"),
    # Adaptation vs Combination (Chapter 6, Lesson 1):
    ("តើបន្សំជាអ្វី", "តើបន្ស៊ាំជាអ្វី"),
    ("លក្ខណៈបន្សំ", "លក្ខណៈបន្ស៊ាំ"),
    ("សត្វរ៉ាព (សត្វស៊ីគេ)", "ប្រេដាទ័រ (សត្វស៊ីគេ)"),
    ("យំឡេងផ្សេងៗ", "បន្លឺសំឡេងផ្សេងៗ"),
    # OCR audit v3: remaining corpus variants. These same term pairs are in
    # OCR_FIXES (scripts/pipeline/clean_text.py) so questions and indexed text share
    # spellings.
    ("ស្ទីចម៉ាត", "ស្ទិចម៉ាត"),
    ("ស្អិតម៉ាស", "ស្ទិចម៉ាត"),
    ("បន្សុំ", "បន្ស៊ាំ"),
    ("លក្ខណៈ បន្សំ", "លក្ខណៈបន្ស៊ាំ"),
    ("ជំងឺហមារីក", "ជំងឺមហារីក"),
]

# "ខួរឆ្អឹង" (bone marrow) is NOT a Grade 12 Biology topic; the textbook only
# uses ខួរឆ្អឹងខ្នង (spinal cord). Students asking about the brain sometimes
# type/OCR ខួរឆ្អឹង as a short form of ខួរធំ (cerebrum, ch.3 l.1 p.67/70-71),
# which retrieves nothing. Rewrite it to ខួរធំ UNLESS it is followed by ខ្នង,
# which guards the legitimate term ខួរឆ្អឹងខ្នង.
_CEREBRUM_RE = re.compile(r"ខួរឆ្អឹង(?!ខ្នង)")

# "រលកសូ" (OK) vs "រលកសូរ" (sound wave, correct). Plain replace() of the
# shorter form would turn the correct "រលកសូរ" into "រលកសូររ"; guard so we
# only fix the OCR/typo form that is missing the final "រ".
_SOUND_WAVE_RE = re.compile(r"រលកសូ(?!រ)")


def normalize_query(text: str) -> str:
    """Rewrite garbled/OCR-style spellings in a student question to the
    canonical terms used in the textbook corpus. Idempotent and safe: no
    legitimate term matches any key."""
    text = (text or "").strip()
    for bad, good in QUERY_FIXES:
        text = text.replace(bad, good)
    text = _SOUND_WAVE_RE.sub("រលកសូរ", text)
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


# Topic synonyms that are true in the textbook but may not appear in the
# student's wording. Appending them (rather than replacing the question) keeps
# the sentence grammatical and gives the retriever the corpus vocabulary.
# Example: pine (ស្រល់) is a gymnosperm whose reproductive structure is a cone;
# without these terms, "ដំណើរការលំអងរបស់ស្រល់" is outranked by the much more
# numerous flowering-plant pollination pages.
_TOPIC_EXPANSIONS = (
    ("ស្រល់", "ស៊ីមណូស្ពែម កោន"),
    # Polished rice is the rice grain's albumen/endosperm. The corpus never
    # uses the student words "អង្ករ"/"សំរូប"; it uses គ្រាប់ស្រូវ (rice grain),
    # អាល់ប៊ុយមែន and អង់ដូស្ពែម (p18). Append that vocabulary so the
    # question can reach the seed pages without changing its meaning.
    ("អង្ករសំរូប", "គ្រាប់ស្រូវ អាល់ប៊ុយមែន អង់ដូស្ពែម"),
)


def _expand_topic_terms(text: str) -> str:
    suffix = [
        extra for term, extra in _TOPIC_EXPANSIONS
        if term in text and extra not in text
    ]
    return (text + " " + " ".join(suffix)).strip() if suffix else text


def expand_query(text: str) -> str:
    """Term normalization + query reshaping used inside the RAG pipeline so
    retrieval scores stay above the abstain threshold. The student's displayed
    message keeps the term-fixed original (see normalize_query)."""
    return _expand_topic_terms(_expand_definition(normalize_query(text)))


# --- Multi-part question splitting -----------------------------------------
# Exam prompts use top-level Roman markers (I., II.) and Khmer sub-markers
# (ក., ខ., គ., ឃ., ង.) in the same message. Keeping a marker in the text sent
# to retrieval/reranking lowers scores (e.g. "I. ..." can fall below the
# abstain threshold), so strip them and retrieve each question separately.
_LEAD_MARKER_RE = re.compile(
    r'^(?:[IVX]{1,6}|[កខគឃងចឆជឈញដឋឌឍណតថទធនបផពភមយរលវសហឡអ]|\d+)[.។]\s*'
)
_ROMAN_TOP_RE = re.compile(r'(?:^|(?<=[។\s]))([IVX]{1,6})[.។]\s*')
_KHMER_SEQUENCE = "កខគឃង"
_KHMER_INLINE_RE = re.compile(r'(?:^|(?<=[\s។?!]))([កខគឃង])[.។]\s*')


def strip_lead_markers(text: str) -> str:
    """Strip leading question-number markers (I., ក., 1., ...) before retrieval."""
    prev = None
    while text != prev:
        prev = text
        text = _LEAD_MARKER_RE.sub('', text)
    return text.strip()


def _split_khmer_subquestions(text: str) -> list[str] | None:
    """Split inline Khmer sub-questions, or return None if not a valid series.

    Only split when at least two markers form the expected ordered series
    ក., ខ., គ., ឃ., ង.; this avoids treating a lone abbreviation or a
    normal consonant followed by a full stop as a question boundary.
    """
    normalized = re.sub(r'(?<=[កខគឃង])[.។](?=\S)', '. ', text)
    markers = list(_KHMER_INLINE_RE.finditer(normalized))
    if len(markers) < 2:
        return None
    letters = [m.group(1) for m in markers]
    if letters != list(_KHMER_SEQUENCE[:len(letters)]):
        return None

    parts = []
    for i, m in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(normalized)
        question = strip_lead_markers(normalized[m.end():end])
        if question:
            parts.append(question)
    return parts or None


def split_questions(text: str) -> list[str]:
    """Split an exam-style message into individual retrieval questions.

    Top-level Roman markers (I., II., ...) are split first; Khmer sub-markers
    (ក., ខ., ...) are then split inside each resulting part. Single questions
    keep their text minus any leading marker.
    """
    text = text or ''
    text = re.sub(r'([IVX]{1,6})[.។](?=\S)', r'\1. ', text)
    markers = list(_ROMAN_TOP_RE.finditer(text))
    if markers:
        roman_parts = []
        for i, m in enumerate(markers):
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            part = text[m.end():end]
            if part.strip():
                roman_parts.append(part)
    else:
        roman_parts = [text]

    parts = []
    for part in roman_parts:
        khmer_parts = _split_khmer_subquestions(part)
        if khmer_parts:
            parts.extend(khmer_parts)
            continue
        cleaned = strip_lead_markers(part)
        if cleaned:
            parts.append(cleaned)
    return parts or [strip_lead_markers(text)]