# KhmerBio Tutor 🧬🇰🇭

**Khmer Grade 12 Biology AI Tutor using LLM + RAG**

KhmerBio Tutor is an AI learning assistant designed to help Cambodian Grade 12 students understand Biology lessons more easily in Khmer. The system uses the official Grade 12 Biology learning materials as its knowledge source and combines them with a Large Language Model (LLM) through Retrieval-Augmented Generation (RAG).

The goal is not to train a new LLM from scratch. Instead, the project builds a reliable educational assistant that retrieves the correct Biology lesson first and then asks an LLM to explain it in simple, student-friendly Khmer.

---

## 1. Project Goal

Build an AI tutor that can:

- Answer Grade 12 Biology questions in Khmer.
- Explain difficult concepts in simple language.
- Use Grade 12 Biology textbook content as the main knowledge source.
- Show the lesson/chapter/page used to produce an answer.
- Support easy explanations, normal explanations, and exam-focused answers.
- Generate summaries and quizzes.
- Avoid inventing answers when the textbook does not contain enough information.
- Help students prepare for school lessons and the Grade 12/Bac II examination.

---

## 2. Project Scope

### Version 1 — Core System

The first version should focus only on:

- Cambodian Grade 12 Biology.
- Text-based questions.
- Khmer answers.
- Textbook-grounded RAG.
- Source citation.
- Simple chatbot interface.
- Quiz and summary modes.

### Version 2 — Optional Improvements

After Version 1 works well, add:

- Biology diagram/image explanation.
- Khmer voice input.
- Khmer text-to-speech.
- Student progress tracking.
- Personalized recommendations.
- Teacher dashboard.
- Mobile/web application.
- Fine-tuned Khmer Biology tutor model.

---

# 3. System Architecture

```text
Grade 12 Biology Textbook / Learning Materials
                    │
                    ▼
             Text Extraction
                    │
                    ▼
              Text Cleaning
                    │
                    ▼
          Chapter / Lesson Parsing
                    │
                    ▼
                Chunking
                    │
                    ▼
            Embedding Model
               (BGE-M3)
                    │
                    ▼
            Vector Database
            (Chroma/Qdrant)
                    │
                    │
Student Question ───┤
                    ▼
             Query Embedding
                    │
                    ▼
              Retrieval
                    │
                    ▼
              Reranking
                    │
                    ▼
        Relevant Biology Context
                    │
                    ▼
                  LLM
                    │
                    ▼
       Simple Khmer Explanation
                    │
                    ▼
                Student
```

---

# 4. Recommended Technology Stack

| Component | Recommended Tool |
|---|---|
| Programming language | Python |
| Backend API | FastAPI |
| First user interface | Streamlit |
| LLM | Multilingual instruction model or API |
| Embedding model | BAAI/bge-m3 |
| Reranker | BAAI/bge-reranker-v2-m3 |
| Vector database | Chroma for MVP |
| PDF extraction | PyMuPDF |
| Data format | JSON / JSONL |
| Testing | Pytest |
| Version control | Git + GitHub |
| Deployment | Streamlit Cloud / Render / Hugging Face Spaces / VPS |

---

# 5. Recommended Project Structure

```text
khmer-biology-ai/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── rag.py
│   ├── retrieval.py
│   ├── reranker.py
│   ├── prompt.py
│   └── utils.py
│
├── data/
│   ├── raw/
│   │   └── biology_grade12.pdf
│   │
│   ├── extracted/
│   │   └── biology_raw_text.json
│   │
│   ├── processed/
│   │   ├── biology_cleaned.json
│   │   └── biology_chunks.json
│   │
│   ├── glossary/
│   │   └── biology_terms.json
│   │
│   └── evaluation/
│       └── evaluation_questions.json
│
├── scripts/
│   ├── extract_pdf.py
│   ├── clean_text.py
│   ├── parse_lessons.py
│   ├── chunk_text.py
│   ├── build_vector_db.py
│   └── test_retrieval.py
│
├── vector_db/
│
├── tests/
│   ├── test_cleaning.py
│   ├── test_retrieval.py
│   └── test_rag.py
│
└── docs/
    ├── architecture.md
    └── evaluation.md
```

---

# 6. Complete Development Roadmap

The project should be completed in the following order.

---

## Phase 0 — Define the Problem Clearly

### Objective

Decide exactly what the first version of the system must do.

### Tasks

1. Define the target users.
   - Grade 12 students in Cambodia.

2. Define the target subject.
   - Grade 12 Biology only.

3. Define the main language.
   - Khmer.

4. Define the main use cases.
   - Ask Biology questions.
   - Explain a lesson.
   - Summarize a topic.
   - Compare concepts.
   - Generate quizzes.
   - Provide exam-focused answers.

5. Define what the system must not do.
   - Do not answer unrelated subjects as if they are part of the Grade 12 Biology textbook.
   - Do not invent textbook information.
   - Do not present uncertain answers as facts.

### Output

A short project specification describing:

```text
Users
Problem
Scope
Features
Limitations
Expected output
```

### Phase 0 is complete when

You can explain the entire project in one clear paragraph.

---

# Phase 1 — Collect the Grade 12 Biology Knowledge Source

### Objective

Collect the trusted material that the AI tutor will use.

### Tasks

1. Obtain the Cambodian Grade 12 Biology textbook.
2. Collect official or trusted Grade 12 Biology learning materials if available.
3. Verify that the content matches the current curriculum you want to support.
4. Check copyright and usage permissions before redistributing textbook content.
5. Store the original materials in:

```text
data/raw/
```

Example:

```text
data/raw/biology_grade12.pdf
```

6. Create an inventory of:
   - chapters,
   - lessons,
   - sections,
   - exercises,
   - diagrams,
   - glossary terms.

### Output

A complete list of the source materials used by the system.

### Phase 1 is complete when

You know exactly which textbook/materials the AI is allowed to use as its knowledge base.

---

# Phase 2 — Extract Text from the Biology PDF

### Objective

Convert the textbook into machine-readable text.

### Tasks

1. Use PyMuPDF to open the PDF.
2. Extract text page by page.
3. Preserve the page number.
4. Preserve chapter titles when possible.
5. Preserve lesson titles when possible.
6. Save the extracted data in structured format.

Recommended format:

```json
{
  "page": 23,
  "chapter": "...",
  "lesson": "...",
  "text": "..."
}
```

7. Manually inspect several pages after extraction.
8. Check whether Khmer characters are extracted correctly.
9. Identify pages where text extraction fails.
10. Handle scanned/image-only pages separately if necessary.

### Output

```text
data/extracted/biology_raw_text.json
```

### Phase 2 is complete when

Most textbook pages are available as readable Khmer text with correct page numbers.

---

# Phase 3 — Clean and Normalize Khmer Text

### Objective

Prepare high-quality Khmer text before creating embeddings.

### Tasks

1. Normalize Unicode.
2. Remove repeated headers and footers.
3. Remove page artifacts.
4. Remove accidental duplicated text.
5. Fix unnecessary whitespace.
6. Preserve useful Khmer punctuation.
7. Preserve scientific symbols and English terms.
8. Preserve headings.
9. Preserve chapter/lesson/page metadata.
10. Manually compare cleaned text with the PDF.

Do not aggressively remove Khmer characters or punctuation.

### Output

```text
data/processed/biology_cleaned.json
```

### Phase 3 is complete when

The cleaned text is easy to read and still matches the original textbook.

---

# Phase 4 — Organize the Textbook by Chapter and Lesson

### Objective

Give the dataset meaningful structure.

### Tasks

For every text section, store metadata such as:

```json
{
  "chapter_id": 1,
  "chapter_title": "...",
  "lesson_id": 1,
  "lesson_title": "...",
  "section_title": "...",
  "page": 23,
  "text": "..."
}
```

Try to organize the textbook in this hierarchy:

```text
Chapter
  └── Lesson
       └── Section
            └── Paragraph
```

### Why this matters

A structured textbook gives the system better retrieval and better citations.

### Output

Structured Biology dataset with chapter, lesson, section, and page metadata.

### Phase 4 is complete when

Every important paragraph belongs to a known lesson or topic.

---

# Phase 5 — Build a Biology Glossary

### Objective

Create a reliable Khmer-English Biology terminology dictionary.

### Tasks

Create records such as:

```json
{
  "term_en": "Chromosome",
  "term_kh": "ក្រូម៉ូសូម",
  "definition_kh": "...",
  "chapter": "..."
}
```

Include important Grade 12 terms such as:

- DNA
- RNA
- Gene
- Chromosome
- Mutation
- Protein
- Enzyme
- Mitosis
- Meiosis
- Genetics

### Output

```text
data/glossary/biology_terms.json
```

### Phase 5 is complete when

The most important Biology terms used in the textbook have consistent Khmer and English names.

---

# Phase 6 — Chunk the Textbook

### Objective

Split the textbook into smaller passages that can be searched efficiently.

### Tasks

1. Chunk by lesson and section instead of randomly cutting text.
2. Keep related sentences together.
3. Start by testing approximately 300–600 tokens per chunk.
4. Add small overlap when needed.
5. Keep metadata with every chunk.

Example:

```json
{
  "chunk_id": "chapter01_lesson02_003",
  "chapter": "...",
  "lesson": "DNA",
  "section": "Structure of DNA",
  "page_start": 23,
  "page_end": 24,
  "text": "..."
}
```

6. Inspect chunks manually.
7. Make sure chunks do not mix unrelated Biology topics.

### Output

```text
data/processed/biology_chunks.json
```

### Phase 6 is complete when

Every textbook topic can be represented by clean, meaningful chunks.

---

# Phase 7 — Create Embeddings

### Objective

Convert Biology chunks into vectors so the system can search by meaning.

### Recommended model

```text
BAAI/bge-m3
```

### Tasks

1. Install the embedding model.
2. Load `biology_chunks.json`.
3. Create an embedding for each chunk.
4. Store each vector with its original text and metadata.
5. Test several Khmer Biology questions.

Example test question:

```text
តើ DNA មានតួនាទីអ្វី?
```

The retrieval system should return passages about DNA function.

### Output

Embeddings for every Biology chunk.

### Phase 7 is complete when

Semantically related Khmer questions return relevant textbook passages.

---

# Phase 8 — Build the Vector Database

### Objective

Store and search textbook embeddings efficiently.

### Recommended MVP database

```text
Chroma
```

### Tasks

1. Create the vector database.
2. Insert all chunk embeddings.
3. Store metadata:
   - chunk ID,
   - chapter,
   - lesson,
   - section,
   - page,
   - original text.
4. Implement semantic search.
5. Test Top-K retrieval.

Example:

```text
Question
  ↓
Embedding
  ↓
Vector Search
  ↓
Top 10 Biology chunks
```

### Output

```text
vector_db/
```

### Phase 8 is complete when

You can enter a Khmer Biology question and retrieve relevant textbook passages.

---

# Phase 9 — Add a Reranker

### Objective

Improve retrieval quality by ranking the retrieved passages again.

### Recommended model

```text
BAAI/bge-reranker-v2-m3
```

### Tasks

1. Retrieve around 10–20 candidate chunks.
2. Send those chunks to the reranker.
3. Score each candidate against the student question.
4. Keep the best 3–5 chunks.

Pipeline:

```text
Question
   ↓
Embedding Search
   ↓
Top 10–20 chunks
   ↓
Reranker
   ↓
Best 3–5 chunks
```

### Output

A retrieval pipeline that returns highly relevant Biology context.

### Phase 9 is complete when

Relevant textbook sections consistently rank above unrelated sections.

---

# Phase 10 — Connect the LLM

### Objective

Use an LLM to explain the retrieved textbook information in clear Khmer.

### Important rule

The LLM should receive the retrieved Biology context before answering.

### Prompt responsibilities

The system prompt should tell the model to:

1. Act as a Cambodian Grade 12 Biology tutor.
2. Explain in simple Khmer.
3. Use the supplied textbook context for curriculum facts.
4. Avoid unsupported claims.
5. Say when the available context is insufficient.
6. Use examples or analogies when useful.
7. Highlight exam-important points.
8. Include textbook source references.

Example RAG input:

```text
SYSTEM:
You are a Grade 12 Biology tutor for Cambodian students.
Use the provided textbook context for factual curriculum claims.
Explain clearly in simple Khmer.
Do not invent information that is not supported by the context.

CONTEXT:
[Retrieved textbook chunks]

QUESTION:
តើ DNA មានតួនាទីអ្វី?
```

### Output

An answer generated from retrieved textbook evidence.

### Phase 10 is complete when

The LLM can produce understandable Khmer explanations while staying grounded in the textbook.

---

# Phase 11 — Design the Student-Friendly Answer Format

### Objective

Make answers easy for Grade 12 students to understand and remember.

### Recommended structure

```text
Title

Simple definition

Easy explanation

Example / analogy

Important points

Exam note

Textbook source

Practice question
```

Example style:

```text
🧬 DNA ជាអ្វី?

[Simple definition]

💡 យល់ងាយៗ
[Simple explanation or analogy]

📌 ចំណុចសំខាន់
1. ...
2. ...
3. ...

🎯 សម្រាប់ការប្រឡង
[Important exam point]

📖 ប្រភព
ជំពូក ... / មេរៀន ... / ទំព័រ ...

❓ សាកល្បងខ្លួនឯង
[One practice question]
```

### Phase 11 is complete when

Students can understand the answer without needing advanced Biology knowledge.

---

# Phase 12 — Add Learning Modes

### Objective

Allow students to learn in different ways.

### Recommended modes

#### 1. Easy Mode

Use very simple Khmer and short explanations.

#### 2. Normal Mode

Provide a complete Grade 12-level explanation.

#### 3. Exam Mode

Provide concise answers focused on important exam concepts.

#### 4. Summary Mode

Summarize a chapter or lesson.

#### 5. Quiz Mode

Generate questions based on the retrieved lesson.

#### 6. Compare Mode

Explain differences between two Biology concepts.

Example:

```text
DNA vs RNA
Mitosis vs Meiosis
Dominant vs Recessive
```

### Phase 12 is complete when

One question can be answered differently depending on the student's learning goal.

---

# Phase 13 — Build the First User Interface

### Objective

Create a simple application students can use.

### Recommended first UI

```text
Streamlit
```

### Main interface

```text
KhmerBio Tutor

[ Ask a Biology question... ]

Mode:
[ Easy ] [ Normal ] [ Exam ]

Learning feature:
[ Explain ] [ Summary ] [ Quiz ] [ Compare ]

[ Send ]
```

### Display

The app should show:

- student question,
- AI explanation,
- lesson/chapter,
- page source,
- important points,
- optional practice question.

### Phase 13 is complete when

A student can ask a question through the browser and receive a grounded Khmer Biology explanation.

---

# Phase 14 — Create an Evaluation Dataset

### Objective

Measure whether the system actually works.

### Recommended size

Start with around 100–200 manually reviewed Grade 12 Biology questions.

### Include different question types

- Definition
- Explanation
- Comparison
- Process
- Reasoning
- Exam-style
- Lesson summary

### Include difficulty levels

```text
Easy
Medium
Hard
```

### Recommended format

```json
{
  "question_id": 1,
  "question_kh": "...",
  "chapter": "...",
  "question_type": "comparison",
  "difficulty": "medium",
  "expected_answer": "...",
  "expected_source_page": 25,
  "expected_concepts": ["...", "..."]
}
```

### Output

```text
data/evaluation/evaluation_questions.json
```

### Phase 14 is complete when

You have a trusted set of questions that can be used to compare system versions.

---

# Phase 15 — Evaluate Retrieval

### Objective

Check whether the system finds the correct textbook sections.

### Suggested metrics

- Recall@1
- Recall@3
- Recall@5
- Mean Reciprocal Rank (MRR)

### Questions to answer

- Does the correct lesson appear in Top 3?
- Does the correct page appear in Top 5?
- Does reranking improve results?
- Which question types are difficult?

### Compare experiments

Test different:

- chunk sizes,
- chunk overlap,
- embedding models,
- Top-K values,
- reranker configurations.

### Phase 15 is complete when

Retrieval reliably finds the textbook content needed to answer the evaluation questions.

---

# Phase 16 — Evaluate Answer Quality

### Objective

Measure the quality of final AI answers.

### Evaluate

| Metric | Meaning |
|---|---|
| Correctness | Is the Biology answer correct? |
| Faithfulness | Is the answer supported by retrieved evidence? |
| Relevance | Does it answer the student's question? |
| Completeness | Does it include the important concepts? |
| Khmer clarity | Is the language easy to understand? |
| Curriculum alignment | Does it match Grade 12 material? |
| Citation accuracy | Is the chapter/page reference correct? |
| Abstention | Does it admit when evidence is missing? |

### Human evaluation

If possible, ask:

- a Biology teacher,
- Grade 12 students,
- university Biology students

to review sample answers.

### Phase 16 is complete when

You have measurable evidence showing which parts of the system work well and which need improvement.

---

# Phase 17 — Improve the RAG Pipeline

### Objective

Improve weak areas identified during evaluation.

### Possible improvements

1. Better chunking.
2. Hybrid search.
3. Metadata filtering.
4. Better Khmer query normalization.
5. Reranking.
6. Query expansion.
7. Biology terminology dictionary.
8. Better prompts.
9. Better source citation handling.
10. Conversation-aware retrieval.

### Important rule

Make one major change at a time and compare it using the same evaluation dataset.

### Phase 17 is complete when

The improved version performs better than the baseline on your evaluation metrics.

---

# Phase 18 — Add Safety and Reliability Rules

### Objective

Prevent misleading or unsupported answers.

### Rules

The system should:

- refuse to invent textbook content,
- clearly state when information is not found,
- separate textbook information from optional extra explanation,
- avoid pretending to know a page number that was not retrieved,
- avoid changing scientific definitions for simplicity,
- clearly label uncertain answers,
- keep student explanations age-appropriate and educational.

Example fallback:

```text
ខ្ញុំមិនបានរកឃើញព័ត៌មានគ្រប់គ្រាន់នៅក្នុងមេរៀនដែលបានផ្តល់ឱ្យ ដើម្បីឆ្លើយសំណួរនេះដោយច្បាស់លាស់ទេ។
```

### Phase 18 is complete when

The system handles missing or uncertain information safely instead of hallucinating.

---

# Phase 19 — Add Testing

### Objective

Make sure future code changes do not break the system.

### Add tests for

- text extraction,
- text cleaning,
- chunk generation,
- metadata,
- embeddings,
- retrieval,
- reranking,
- prompt formatting,
- source citations,
- API responses.

### Phase 19 is complete when

Core project components can be tested automatically.

---

# Phase 20 — Build the Backend API

### Objective

Separate the AI logic from the user interface.

### Recommended framework

```text
FastAPI
```

### Possible endpoints

```text
POST /ask
POST /quiz
POST /summary
POST /compare
GET  /chapters
GET  /lessons
GET  /health
```

### Example request

```json
{
  "question": "តើ DNA មានតួនាទីអ្វី?",
  "mode": "easy"
}
```

### Example response

```json
{
  "answer": "...",
  "chapter": "...",
  "lesson": "...",
  "pages": [23, 24],
  "sources": ["..."]
}
```

### Phase 20 is complete when

The AI tutor can be used through an API independently from Streamlit.

---

# Phase 21 — Improve the User Experience

### Objective

Make the application comfortable for real students.

### Features

- Khmer-friendly font.
- Mobile-friendly layout.
- Conversation history.
- Suggested questions.
- Chapter selection.
- Lesson selection.
- Clear loading state.
- Copy answer button.
- Feedback buttons.
- Easy/Normal/Exam mode selector.
- Source viewer.

### Phase 21 is complete when

Students can use the system without technical knowledge.

---

# Phase 22 — User Testing with Students

### Objective

Validate whether the system is actually useful for learning.

### Suggested test

Ask Grade 12 students to use the system for several Biology topics.

Collect feedback about:

- answer clarity,
- answer correctness,
- Khmer language quality,
- usefulness,
- response length,
- source references,
- quiz usefulness,
- interface usability.

Example rating scale:

```text
1 = Very poor
2 = Poor
3 = Acceptable
4 = Good
5 = Very good
```

### Phase 22 is complete when

You have real student feedback and a list of improvements based on their experience.

---

# Phase 23 — Optional Fine-Tuning

### Objective

Improve the teaching style after the RAG system already works well.

Do not start with fine-tuning.

Fine-tuning should be considered only when you have a high-quality dataset of ideal tutor responses.

### Training data format

```text
Question
+
Retrieved textbook context
+
Ideal Khmer teacher explanation
```

Possible dataset size:

```text
1,000–5,000 high-quality examples
```

### Use fine-tuning mainly for

- Khmer teaching style,
- answer structure,
- simplified explanations,
- exam-answer formatting,
- consistent terminology.

Remember:

```text
RAG teaches the model WHAT information to use.
Fine-tuning teaches the model HOW to answer.
```

### Phase 23 is complete when

The fine-tuned model performs better than the original model on the same evaluation set.

---

# Phase 24 — Optional Multimodal Biology Tutor

### Objective

Allow students to upload Biology diagrams or images.

### Example questions

- Explain this DNA diagram.
- Which stage of mitosis is this?
- What part of the cell is shown here?
- Explain this genetic cross.

### Requirements

Use a multimodal LLM that supports image + text input.

### Important

Keep the original text RAG pipeline. Image understanding should be an additional feature, not a replacement for textbook grounding.

### Phase 24 is complete when

A student can upload a Biology diagram and receive a useful explanation linked to relevant Grade 12 content.

---

# Phase 25 — Deployment

### Objective

Make the application accessible online.

### Deployment options

For a simple demo:

- Streamlit Cloud
- Hugging Face Spaces

For a separated frontend/backend application:

- Frontend hosting
- FastAPI backend hosting
- Hosted vector database or persistent storage

### Before deployment

Check:

- environment variables,
- API keys,
- model access,
- database persistence,
- error handling,
- CORS,
- rate limiting,
- logs,
- privacy,
- textbook usage rights.

### Phase 25 is complete when

Students can open a public or private URL and use the Biology tutor successfully.

---

# Phase 26 — Final Project Evaluation

### Objective

Produce the final results for the project report or presentation.

### Final experiments should include

1. Baseline retrieval.
2. Improved retrieval.
3. Retrieval + reranker.
4. Final RAG answer quality.
5. Human evaluation.
6. Student usability feedback.

### Final report metrics

Include:

- retrieval Recall@K,
- answer correctness,
- faithfulness,
- Khmer clarity,
- curriculum alignment,
- citation accuracy,
- student satisfaction.

### Final analysis

Document:

- what worked,
- what failed,
- limitations,
- lessons learned,
- future improvements.

### Phase 26 is complete when

You can clearly demonstrate that the system helps Grade 12 students understand Biology concepts more easily.

---

# 7. Development Order Summary

Follow this order strictly:

```text
1. Define project scope
       ↓
2. Collect textbook/materials
       ↓
3. Extract PDF text
       ↓
4. Clean Khmer text
       ↓
5. Organize chapters and lessons
       ↓
6. Build Biology glossary
       ↓
7. Chunk the textbook
       ↓
8. Generate embeddings
       ↓
9. Build vector database
       ↓
10. Test retrieval
       ↓
11. Add reranker
       ↓
12. Connect LLM
       ↓
13. Build RAG pipeline
       ↓
14. Add source citations
       ↓
15. Design answer format
       ↓
16. Add learning modes
       ↓
17. Build Streamlit interface
       ↓
18. Create evaluation dataset
       ↓
19. Evaluate retrieval
       ↓
20. Evaluate answers
       ↓
21. Improve RAG
       ↓
22. Add safety rules
       ↓
23. Add automated tests
       ↓
24. Build FastAPI backend
       ↓
25. Improve UI/UX
       ↓
26. Test with Grade 12 students
       ↓
27. Optional fine-tuning
       ↓
28. Optional image/diagram support
       ↓
29. Deploy application
       ↓
30. Final evaluation and report
```

---

# 8. Suggested Milestones

## Milestone 1 — Dataset Ready

Complete:

- textbook collection,
- extraction,
- cleaning,
- lesson organization,
- chunking.

Result:

```text
biology_chunks.json
```

---

## Milestone 2 — Retrieval Works

Complete:

- embeddings,
- vector database,
- semantic search,
- reranking.

Result:

A Khmer Biology question retrieves the correct textbook section.

---

## Milestone 3 — RAG Tutor Works

Complete:

- LLM integration,
- prompt design,
- textbook grounding,
- source citation.

Result:

The system produces understandable Khmer Biology answers based on textbook evidence.

---

## Milestone 4 — Student App Works

Complete:

- Streamlit UI,
- Easy mode,
- Normal mode,
- Exam mode,
- Quiz mode,
- Summary mode.

Result:

Students can interact with the tutor through a browser.

---

## Milestone 5 — System Is Evaluated

Complete:

- evaluation dataset,
- retrieval evaluation,
- answer evaluation,
- human review,
- student testing.

Result:

You have measurable evidence of system quality.

---

## Milestone 6 — Final Product

Complete:

- improvements,
- testing,
- backend,
- deployment,
- documentation,
- final report.

Result:

A complete Khmer Grade 12 Biology AI Tutor prototype.

---

# 9. Minimum Viable Product (MVP)

Do not build every feature immediately.

The first working version only needs:

```text
1 Grade 12 Biology textbook
        ↓
Clean chunks
        ↓
BGE-M3 embeddings
        ↓
Chroma
        ↓
Retriever
        ↓
Reranker
        ↓
LLM
        ↓
Khmer answer + textbook source
        ↓
Streamlit chatbot
```

MVP features:

- Ask a Khmer Biology question.
- Retrieve relevant textbook content.
- Answer in simple Khmer.
- Show source chapter/lesson/page.
- Avoid unsupported answers.

Complete the MVP before adding advanced features.

---

# 10. Important Project Principles

### 1. Do not train an LLM from scratch

Use an existing multilingual LLM first.

### 2. Build RAG before fine-tuning

The textbook should provide the knowledge.

### 3. Data quality is more important than UI design

Poorly extracted textbook data will produce poor answers.

### 4. Evaluate retrieval separately from generation

If the answer is wrong, first determine whether:

- retrieval found the wrong passage, or
- the LLM misunderstood the correct passage.

### 5. Keep sources

Every chunk should preserve chapter, lesson, and page information.

### 6. Do not trust one embedding model automatically

Evaluate models using real Khmer Biology questions.

### 7. Keep the project narrow at first

Grade 12 Biology only.

### 8. Measure improvements

Do not say a new version is better without comparing it on the same test set.

---

# 11. Final Success Criteria

The project can be considered successful when:

- Grade 12 students can ask questions in Khmer.
- The system retrieves the correct Biology lesson most of the time.
- Answers are scientifically correct.
- Answers are easy for Grade 12 students to understand.
- Answers stay grounded in the textbook.
- Sources are displayed correctly.
- The system avoids hallucinating when information is missing.
- Students find the system useful for learning.
- Evaluation results are documented.
- The application can be demonstrated reliably.

---

# 12. Future Features

After the main project is complete, possible extensions include:

- Grade 10 Biology.
- Grade 11 Biology.
- Chemistry tutor.
- Physics tutor.
- Khmer speech-to-text.
- Khmer text-to-speech.
- Diagram understanding.
- Personalized student profiles.
- Learning history.
- Weak-topic detection.
- Adaptive quizzes.
- Teacher analytics dashboard.
- Offline local model support.
- Mobile application.

---

# 13. Final Project Vision

```text
Khmer Grade 12 Student
        ↓
Ask a Biology question in Khmer
        ↓
AI searches trusted Grade 12 Biology material
        ↓
AI finds the correct lesson
        ↓
AI explains the concept in simple Khmer
        ↓
Student sees important points + textbook source
        ↓
Student practices with a quiz
        ↓
Student understands the lesson more easily
```

**KhmerBio Tutor is not intended to replace teachers. It is designed to be a learning assistant that helps students understand Grade 12 Biology concepts more clearly, practice independently, and access curriculum-grounded explanations when they need help.**
