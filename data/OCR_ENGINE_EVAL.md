# OCR ENGINE EVALUATION  (2026-09-08)  -- page 5 = known-good reference (Gemini)
# Reference chars: 758 (clean Khmer).  Tesseract chars: 836.
SRC:
  reference: data/extracted/biology_raw_text.jsonl page 5 (Gemini OCR, validated clean)
  local tesseract: tesseract.exe -l khm --psm 6, tessdata_best/khm.traineddata @400dpi grayscale
RESULT (page 5):
  Tesseract: ratio 0.673 char-similarity vs Gemini reference (536/758 exact)
  Failures: "ថ្នាក់"->"ផ្ទាក់" "គ្រាប់"->"ត្រាប់" "រុក្ខជាតិ"->"រ៉ុក្ខជាតិ"
            "ស្វាយ"->"សាយ" "50 000" digit wrong (250000->240000)
  Also spurious noise chars per line (|-!~3 4 1) from figure overlays
VERDICT: all free-local OCR options insufficient:
  ollama gemma3:4b / qwen2.5vl:7b  -> hallucination loops (recorded earlier)
  tesseract + tessdata_best/khm    -> 67% char accuracy, wrong numerals
  easyocr 'kh'                     -> "not supported" (no Khmer model)
  paddleocr                        -> no Python 3.14 wheel
  rapidocr 3.9.2                   -> lang set has no Khmer (see model_resolver.py)
CONSTRAINT: Gemini 20 free pages/day (per model, generate_content_free_tier_requests)
PLAN: resumable daily OCR runner using Gemini (validated quality, ~1 page/api-call)
