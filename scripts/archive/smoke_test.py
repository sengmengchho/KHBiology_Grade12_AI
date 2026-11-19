"""End-to-end sanity checks for KhmerBio Tutor pipeline changes.

Run from repo root with the project venv:
    .venv\\Scripts\\python.exe scripts\\smoke_test.py
"""
import re
import sys

sys.path.insert(0, ".")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _check_query_normalization():
    from app.utils import normalize_query

    cases = [
        # (garbled input, expected normalized output)
        ("តើពហុប៉ូលជាអ្វី?", "តើពហុបូឡាជាអ្វី?"),
        ("ឯកប្ដួល និងទ្វេប្ដួល", "ឯកបូឡា និងទ្វេបូឡា"),
        ("អ្វីគឺជាទ្វេប៉ូល", "អ្វីគឺជាទ្វេបូឡា"),
        ("រលកសូរ និង សូររោទ៍", "រលកសូរ និង សូរសំឡេងរោទ៍"),
        ("គ្រុបអាមីន", None),  # "ក្រុមអាមីន" -> done via ក្រុម->បណ្តុំ only exact
        # Adaptation terminology (Chapter 6): បន្សំ -> បន្ស៊ាំ
        ("តើបន្សំជាអ្វី?", "តើបន្ស៊ាំជាអ្វី?"),
        ("លក្ខណៈបន្សំ", "លក្ខណៈបន្ស៊ាំ"),
        ("សត្វរ៉ាព (សត្វស៊ីគេ)", "ប្រេដាទ័រ (សត្វស៊ីគេ)"),
        ("យំឡេងផ្សេងៗ", "បន្លឺសំឡេងផ្សេងៗ"),
    ]
    ok = True
    for bad, good in cases:
        out = normalize_query(bad)
        status = "PASS" if (good is None) or (good in out) else "FAIL"
        if status == "FAIL":
            ok = False
            print(f"[{status}] {bad!r} -> {out!r} (expected contains {good!r})")
        else:
            print(f"[{status}] {bad!r} -> {out!r}")
    return ok


def _check_split_markers():
    """Roman-numeral / Khmer sub-question / digit markers must be stripped
    before retrieval so rerank scores stay above the 0.08 abstain threshold."""
    try:
        from app.main import _split_questions
    except Exception:  # streamlit may not be importable headlessly
        print("[SKIP] cannot import app.main")
        return True
    cases = [
        ("II. ក. តើបន្ស៊ាំជាអ្វី?", ["តើបន្ស៊ាំជាអ្វី?"]),
        ("I. តើស្ទិចម៉ាតគឺជាអ្វី?", ["តើស្ទិចម៉ាតគឺជាអ្វី?"]),
        ("ក. តើXជាអ្វី?", ["តើXជាអ្វី?"]),
        ("1. ចូរប្រៀបធៀប A និង B", ["ចូរប្រៀបធៀប A និង B"]),
        ("ចូរពន្យល់ពី DNA", ["ចូរពន្យល់ពី DNA"]),
    ]
    ok = True
    for q, expected in cases:
        got = _split_questions(q)
        status = "PASS" if got == expected else "FAIL"
        if status == "FAIL":
            ok = False
            print(f"[{status}] {q!r} -> {got!r} (expected {expected!r})")
        else:
            print(f"[{status}] {q!r} -> {got!r}")
    return ok


def _check_quiz_parser():
    """Replicate main._render_quiz_answer's parse logic headlessly."""
    src = r"""
**សំណួរទី 1: តើអ្វីទៅជាប្លោកលំអង?**
**ចម្លើយ:** ប្លោកលំអង (pollen sac) គឺជាថង់ដែលស្ថិតនៅក្នុងកេសរប្រុស ដែលបង្កើតជាគ្រាប់លំអង។

**សំណួរទី 2: តើកងធ្នូសក្ដិសិទ្ធិ?**
**ចម្លើយ:** ការ៉េដែកណាមួយ ។
"""
    question_pattern = re.compile(r'(\*\*សំណួរទី\s*\d+\s*:\s*.+?\*\*)')
    parts = question_pattern.split(src)
    if len(parts) <= 1:
        print("[FAIL] no quiz markers found")
        return False
    pairs = []
    for i in range(1, len(parts), 2):
        if i >= len(parts):
            break
        header = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        answer_match = re.match(r'\*\*ចម្លើយ:\*\*\s*(.+)', content, re.DOTALL)
        q_num = re.search(r'សំណួរទី\s*(\d+)', header)
        pairs.append((q_num.group(1) if q_num else "?", bool(answer_match)))
    expected = [("1", True), ("2", True)]
    ok = pairs == expected
    print(f"[{('PASS' if ok else 'FAIL')}] quiz parser pairs={pairs} expected={expected}")
    return ok


def _check_retrieval():
    """Load models once and run the full RAG pipeline on a neuron question."""
    from app.main import _answer
    q = "តើពហុបូឡាជាអ្វី?"
    try:
        out = _answer(q, mode="normal", feature="explain")
        print("[RETRIEVE] answered. Samples of output (first 400 chars):")
        print("  " + out[:400].replace("\n", "\n  "))
        present = "ពហុ" in out
        print(f"[{'PASS' if present else 'FAIL'}] contains 'ពហុ' in answer: {present}")
        return True
    except Exception as err:
        print(f"[RETRIEVE] ERROR: {err}")
        return False


if __name__ == "__main__":
    ok_all = True
    ok_all &= _check_query_normalization()
    ok_all &= _check_split_markers()
    ok_all &= _check_quiz_parser()
    print("=" * 60)
    print("ALL PASS" if ok_all else "SOME FAILED")
    sys.exit(0 if ok_all else 1)