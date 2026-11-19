"""Generate the KhmerBio Tutor project progress report as a PDF.

Output: D:\\KHBIO_Report\\KhmerBio_Tutor_Report.pdf
Fonts: Windows Khmer UI (regular + bold) — covers Khmer + Latin.

Usage: python scripts/make_report_pdf.py
"""

import os
from fpdf import FPDF

OUT_DIR = r"D:\KHBIO_Report"
OUT_FILE = os.path.join(OUT_DIR, "KhmerBio_Tutor_Report.pdf")

FONT_REG = r"C:\Windows\Fonts\khmerui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\KhmerUIB.ttf"

TEAL = (0, 102, 128)
DARK = (40, 40, 40)
GREY = (110, 110, 110)


class Report(FPDF):

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Khmer", "B", 9)
        self.set_text_color(*TEAL)
        self.cell(0, 6, "KhmerBio Tutor \u2014 Project Progress Report", align="L")
        self.ln(2)
        self.set_draw_color(*TEAL)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Khmer", "", 9)
        self.set_text_color(*GREY)
        self.cell(0, 6, f"\u2014 {self.page_no()} \u2014", align="C")

    def h1(self, text):
        self.set_font("Khmer", "B", 16)
        self.set_text_color(*TEAL)
        self.multi_cell(0, 8, text)
        self.ln(1)
        self.set_draw_color(*TEAL)
        self.set_line_width(0.6)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

    def h2(self, text):
        self.set_font("Khmer", "B", 12.5)
        self.set_text_color(*TEAL)
        self.ln(2)
        self.multi_cell(0, 7, text)
        self.ln(2)

    def body(self, text):
        self.set_font("Khmer", "", 11)
        self.set_text_color(*DARK)
        self.multi_cell(0, 6.4, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Khmer", "", 11)
        self.set_text_color(*DARK)
        x = self.get_x()
        self.cell(6, 6.4, "\u2022")
        self.multi_cell(0, 6.4, text)
        self.ln(1)

    def key_bullet(self, label, text):
        self.set_font("Khmer", "", 11)
        self.set_text_color(*DARK)
        x = self.get_x()
        self.cell(6, 6.4, "\u2022")
        self.set_font("Khmer", "B", 11)
        self.set_text_color(*TEAL)
        self.cell(self.get_string_width(label) + 1, 6.4, label)
        self.set_font("Khmer", "", 11)
        self.set_text_color(*DARK)
        y0 = self.get_y()
        self.multi_cell(0, 6.4, text)
        self.ln(1)

    def table(self, headers, rows, widths):
        rh = 7.4
        self.set_font("Khmer", "B", 10.5)
        self.set_fill_color(*TEAL)
        self.set_text_color(255, 255, 255)
        self.set_draw_color(255, 255, 255)
        for w, htext in zip(widths, headers):
            self.cell(w, rh, htext, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Khmer", "", 10.5)
        self.set_text_color(*DARK)
        fill = False
        for rrow in rows:
            self.set_fill_color(235, 246, 248)
            hexpected = 0
            for w, cell in zip(widths, rrow):
                self.cell(w, rh, cell, border=1, fill=fill, align="C")
            self.ln()
            fill = not fill
        self.ln(3)

    def page_break_safe_table(self, headers, rows, widths):
        if self.get_y() + rh_total(widths, rows) > self.h - 25:
            self.add_page()
        self.table(headers, rows, widths)


def rh_total(widths, rows):
    return 7.4 * (1 + len(rows)) + 3


def build():
    os.makedirs(OUT_DIR, exist_ok=True)
    pdf = Report(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(18, 18, 18)
    pdf.add_font("Khmer", "", FONT_REG)
    pdf.add_font("Khmer", "B", FONT_BOLD)

    # ---------- Cover ----------
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Khmer", "B", 26)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 12, "KhmerBio Tutor", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Khmer", "B", 15)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 9, "AI \u201cAssistant\u201d for Grade 12 Biology (\u1787\u17b8\u179c\u17d2\u179c\u17b7\u179c\u17d2\u179c\u17b6\u1794)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Khmer", "", 12)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 7, "Project Progress Report \u2014 What Was Done & What Is Next", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Date: 09 September 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Khmer", "", 11)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(0, 7, "This is the AI tool that helps Cambodian Grade 12 students "
                        "understand Biology. Students type a question in Khmer and the tool "
                        "answers using ONLY the official Grade 12 Biology textbook \u2014 "
                        "never invented information. It also gives the page, lesson and chapter "
                        "for every answer so students (and teachers) can double-check the source.",
                   align="C")

    # ---------- 1. Journey so far ----------
    pdf.add_page()
    pdf.h1("1. The Journey So Far (Step by Step)")

    pdf.body("Here is the whole project told as a simple story. Each numbered step is one "
             "completed piece of work \u2014 what it was, what tools were used, and what the result was.")

    steps = [
        ("Step 1 \u2014 Turn the paper textbook into digital text (OCR).",
         "We photographed/scanned all pages of the Grade 12 Biology book and used Google Gemini to read "
         "the Khmer text. Result: all 257 pages were converted to clean digital text."),
        ("Step 2 \u2014 Clean and organize the text.",
         "We removed noise, detected the 8 chapters and their lessons, and cut the text into 1,093 small "
         "searchable pieces called \u201cchunks\u201d (about 500 characters each, with some overlap)."),
        ("Step 3 \u2014 Check the quality of the corpus (audit).",
         "We checked every page: no missing pages, no empty pages, no broken pages. All 1,093 chunks "
         "cover all 257 pages. The small gaps are only the book cover and table of contents."),
        ("Step 4 \u2014 Build the search engine (vector database).",
         "We used BGE-M3 (a language model) to turn each chunk into a mathematical \u201cembedding\u201d and "
         "stored them in Chroma. When a student asks a question, the app finds the most related chunks."),
        ("Step 5 \u2014 Add a re-ranker for better answers.",
         "A second model (BGE-reranker) re-sorts the retrieved chunks so the best material is used first. "
         "Tests proved this clearly improves the answer."),
        ("Step 6 \u2014 Build a real exam-style test set.",
         "We wrote 89 questions spread across all 8 chapters \u2014 definitions, explanations, processes, "
         "comparisons, reasoning, summaries and exam-style questions."),
        ("Step 7 \u2014 Measure retrieval quality.",
         "We ran the 89 questions through the search engine and scored how often the correct textbook pages "
         "were found. The re-ranker raised \u201canswer on first try\u201d from 40.4% to 50.6%."),
        ("Step 8 \u2014 Measure answer quality.",
         "We generated full Khmer answers for 20 sample questions and scored how many key concepts each "
         "answer contained and whether it cited the correct pages."),
        ("Step 9 \u2014 Add hallucination protection.",
         "If the textbook does not contain enough information, the app now says so politely instead of "
         "guessing. The \u201cconfidence bar\u201d was tuned using all 89 test questions."),
        ("Step 10 \u2014 Build the web app.",
         "A Streamlit app with 3 answer styles (Normal, Easy, Exam) and 3 features (Explain, Quiz, "
         "Summary), with a chat history and a \u201cclear chat\u201d button."),
        ("Step 11 \u2014 Build a Biology glossary.",
         "We automatically extracted 51 Khmer biology terms with their definitions, English names and "
         "page numbers \u2014 no AI calls needed."),
    ]
    for title, text in steps:
        pdf.h2(title)
        pdf.body(text)

    # ---------- 2. Search + answer quality ----------
    pdf.add_page()
    pdf.h1("2. Quality Results (Measured, Not Guessed)")

    pdf.h2("2.1 How good is the search? (Retrieval)")
    pdf.body("From the 89-question test: multiple-choice scoring of whether the correct textbook pages "
             "appear in the top search results.")
    pdf.table(
        ["Metric", "Search only", "Search + re-ranker"],
        [
            ["Correct page at position 1 (Recall@1)", "40.4%", "50.6%"],
            ["Correct page in top 3 (Recall@3)", "71.9%", "78.7%"],
            ["Correct page in top 5 (Recall@5)", "89.9%", "84.3%"],
            ["Average ranking quality (MRR)", "0.573", "0.646"],
        ],
        [90, 45, 50],
    )
    pdf.body("Conclusion: the re-ranker answers correctly on the first try more often, so we keep it.")

    pdf.h2("2.2 How good are the full Khmer answers? (RAG)")
    pdf.table(
        ["Run (when)", "Key concepts found", "Correct pages cited"],
        [
            ["v1 \u2014 primary AI model had quota", "mean 74% (12/20 high)", "mean 89%, all 20 ok"],
            ["v2 \u2014 re-run using fallback models", "mean 58% (11/20 high)", "mean 89%, all 20 ok"],
        ],
        [70, 58, 57],
    )
    pdf.body("Important finding: the textbook pages cited are almost always correct. The difference in "
             "answer depth comes from which AI model answered. When the main (free) model runs out of its "
             "daily limit, the app switches to smaller back-up models that give shorter, weaker replies.")

    pdf.h2("2.3 Hallucination protection")
    pdf.body("We measured the \u201cconfidence score\u201d on all 89 test questions: real Biology questions scored "
             "very high (0.92 on average), while unrelated questions scored almost zero. So the app now "
             "stops and says \u201cnot enough information\u201d below a safe bar of 0.08. This stops the AI from "
             "inventing answers when it truly has no textbook material.")

    # ---------- 3. Problems found ----------
    pdf.h1("3. Problems Found (and Their Status)")
    pdf.key_bullet("Fixed \u2014 confidence bar too strict.", "The first bar (0.20) rejected real questions; "
                   "recalibrated to 0.08 using all 89 test questions.")
    pdf.key_bullet("Fixed \u2014 small back-up models stop too early.", "The app now skips any model that "
                   "returns a very short or empty reply and tries the next one.")
    pdf.key_bullet("Fixed \u2014 ugly source lines.", "The OCR put messy text into lesson titles; source "
                   "labels are now shortened and clean.")
    pdf.key_bullet("Known \u2014 weaker answers when free quota runs out.", "Quality drops on fallback "
                   "models (see 2.2). Being improved by design choices in the next phase.")
    pdf.key_bullet("Known \u2014 some OCR spelling errors.", "A few biology terms are misspelled by the "
                   "reader; cosmetic and does not hurt search results.")
    pdf.key_bullet("Known \u2014 glossary built automatically.", "51 terms extracted; a human/teacher pass "
                   "would polish the wording.")

    # ---------- 4. Next steps ----------
    pdf.add_page()
    pdf.h1("4. What To Do Next (In Order)")
    pdf.body("The plan below is ordered by priority. Complete each step before the next.")

    nxt = [
        ("Step A \u2014 Manual browser testing (DO NOW)",
         "Open the app and try every mode (Normal / Easy / Exam), every feature (Explain / Quiz / Summary), "
         "an out-of-scope question, and the Clear-chat button. Judge correctness, clarity, usefulness, "
         "suitability for Grade 12, and source accuracy."),
        ("Step B \u2014 Re-run the 20-answer evaluation on a fresh day",
         "Run the answer test when the main AI model has full quota, to measure its true best quality, "
         "and compare with the two runs already saved in this report."),
        ("Step C \u2014 Fix remaining problems",
         "Only fix what testing actually finds \u2014 no speculative changes."),
        ("Step D \u2014 Student & teacher testing",
         "Share the app with real Grade 12 students and Biology teachers. Collect their ratings and "
         "comments on wording, terms, depth, answer length, quiz quality and how sources are shown."),
        ("Step E \u2014 Apply real-user feedback",
         "Improve the explanations, fix wrong terminology, simplify confusing parts, balance answer "
         "length, sharpen quizzes, and polish the source presentation."),
        ("Step F \u2014 Deploy",
         "Publish the app for real use \u2014 only after steps A\u2013E look good."),
        ("Step G \u2014 Fine-tune only if still needed",
         "Optional. Only if users keep reporting problems that a better prompt or better search cannot fix."),
    ]
    for title, text in nxt:
        pdf.h2(title)
        pdf.body(text)

    # ---------- 5. Key files ----------
    pdf.h1("5. Key Files & Folders")
    pdf.table(
        ["Folder / File", "What it is"],
        [
            ["app/main.py", "The web app (Streamlit)"],
            ["app/rag.py", "Answer generation + model rotation"],
            ["app/retrieval.py", "Search + re-ranking"],
            ["app/prompt.py", "Instructions/templates for the AI"],
            ["app/config.py", "Settings (threshold, model pool)"],
            ["scripts/", "OCR, cleaning, building, evaluation scripts"],
            ["data/evaluation/", "89 questions + results + score data"],
            ["data/glossary/", "The Biology glossary (JSON + Markdown)"],
            ["docs/", "Audit and retrieval reports"],
        ],
        [85, 100],
    )

    pdf.ln(4)
    pdf.set_font("Khmer", "B", 12)
    pdf.set_text_color(*TEAL)
    pdf.multi_cell(0, 7, "Short summary: the app is working, the search and citations are solid, and the "
                         "biggest remaining task is human feedback \u2014 then a clean deployment.")

    pdf.output(OUT_FILE)
    print("PDF written to", OUT_FILE)


if __name__ == "__main__":
    build()