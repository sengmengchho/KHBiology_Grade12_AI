"""Apply the evidence-audited v3.1 gold-label corrections.

Run:  python scripts/update_gold_v3_1.py
Writes: data/evaluation/gold_label_changes_v3_1.json
Idempotent: entries already at the new value are left unchanged.
"""

import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLD = os.path.join(BASE, "data", "evaluation", "gold_questions_v2.json")
LOG = os.path.join(BASE, "data", "evaluation", "gold_label_changes_v3_1.json")

CHANGES = [
    {
        "question_id": 68,
        "old_pages": [150],
        "new_pages": [149, 150],
        "evidence": (
            "p149 (chapter 5 opener): 'មេបាតែងតែបញ្ជូនលក្ខណៈរបស់ខ្លួន "
            "(លក្ខណៈតំណពូជ)ទៅឱ្យកូនចៅខ្លួនជានិច្ច' — parents always transmit "
            "their inherited traits to their offspring. p150 is the lesson "
            "opener/objectives and does not explain the transmission process."
        ),
        "reason": (
            "The direct textbook statement answering parent-to-child inheritance "
            "is on p149; the old [150]-only label was too narrow."
        ),
    },
    {
        "question_id": 78,
        "old_pages": [150, 155, 160, 165, 175],
        "new_pages": [174],
        "evidence": (
            "p174 lesson summary: 'សែនជាអង្គធាតុមួយរបស់ ADN ដែលផ្ទុកព័ត៌មាន"
            "សេនេទិចកំណត់សំយោគប្រតេអ៊ីនប្រភេទមួយ' — the exact gene definition. "
            "p175 only asks 'ដូចម្តេចដែលហៅថាសែន?' as an exercise; p150/155/160 "
            "cover ADN structure and p165 covers ARN, not the gene definition."
        ),
        "reason": (
            "The old labels pointed to lesson openers, ADN-structure pages and an "
            "ARN page. The only page that defines a gene is p174."
        ),
    },
    {
        "question_id": 84,
        "old_pages": [150, 165],
        "new_pages": [150, 160, 165],
        "evidence": (
            "p160 is the ADN lesson summary: it lists ADN as genetic material, "
            "the double helix, nucleotides A/T/C/G and semi-conservative "
            "replication. p165 lists the three ARN types (ARNm, ARNt, ARNr). "
            "p150 is only the ADN lesson opener."
        ),
        "reason": (
            "A quiz-generation question about ADN and ARN needs the ADN content "
            "summary (p160) as well as the ARN page; the old label omitted it."
        ),
    },
    {
        "question_id": 86,
        "old_pages": [26],
        "new_pages": [26, 27, 40],
        "evidence": (
            "p26 is the lesson opener and only lists 'ការស្រូបទឹកពីក្នុងដី' as an "
            "objective. p27 teaches the mechanism: 'រុក្ខជាតិមានសរសៃរស្រូបយកទឹក"
            "ពីក្នុងដីតាមរយៈរោមជញ្ជក់នៃប្ដូរ'. p40 lesson summary restates that "
            "fibrous plants absorb soil water through root hairs."
        ),
        "reason": (
            "The old [26]-only label pointed at objectives, not the lesson content; "
            "p27 and the p40 summary contain the facts needed to create quiz questions."
        ),
    },
    {
        "question_id": 115,
        "old_pages": [150, 165],
        "new_pages_by_part": [[150, 160], [164, 165]],
        "evidence": (
            "Part 0 asks 'តើ ADN ជាអ្វី?': p150 introduces ADN as genetic material "
            "and p160 is the ADN lesson summary (structure, nucleotides, replication). "
            "Part 1 asks 'តើ ARN មានប៉ុន្មានប្រភេទ?': p164 introduces ARN and p165 "
            "states the three functional types ARNm/ARNt/ARNr. p165 does not answer "
            "the ADN definition part."
        ),
        "reason": (
            "The shared [150,165] label made part 0 depend on an ARN page. Split the "
            "gold per part so each sub-question is scored against its own evidence."
        ),
    },
]


def main():
    with open(GOLD, encoding="utf-8") as f:
        gold = json.load(f)
    by_id = {q["question_id"]: q for q in gold}
    applied = []
    for change in CHANGES:
        q = by_id[change["question_id"]]
        if "new_pages" in change:
            current = q.get("expected_source_pages", [])
            if current == change["new_pages"]:
                print(f"q{change['question_id']}: already updated")
                continue
            if current != change["old_pages"]:
                raise SystemExit(
                    f"q{change['question_id']}: unexpected current pages {current}"
                )
            q["expected_source_pages"] = change["new_pages"]
            q["notes"] = (
                (q.get("notes") or "").strip()
                + (" " if q.get("notes") else "")
                + f"Page-label audit v3.1: {change['reason']}"
            ).strip()
        else:
            current = q.get("expected_source_pages_by_part")
            if current == change["new_pages_by_part"]:
                print(f"q{change['question_id']}: already updated")
                continue
            q["expected_source_pages_by_part"] = change["new_pages_by_part"]
            q["notes"] = (
                (q.get("notes") or "").strip()
                + (" " if q.get("notes") else "")
                + f"Per-part gold audit v3.1: {change['reason']}"
            ).strip()
        applied.append(change)
        print(f"q{change['question_id']}: updated")

    with open(GOLD, "w", encoding="utf-8") as f:
        json.dump(gold, f, ensure_ascii=False, indent=2)

    if applied:
        existing = []
        if os.path.exists(LOG):
            with open(LOG, encoding="utf-8") as f:
                existing = json.load(f)
        existing.extend(applied)
        with open(LOG, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"Wrote {LOG} ({len(existing)} entries)")
    else:
        print("No changes applied.")


if __name__ == "__main__":
    main()
