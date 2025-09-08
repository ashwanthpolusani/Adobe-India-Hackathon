# 🚀 Adobe India Hackathon Project – PDF Intelligence Suite

Welcome to our team submission for the **Adobe India Hackathon**!  
This repository contains solutions for both **Challenge 1A** (PDF Outline Extraction) and **Challenge 1B** (Multi-Collection PDF Intelligence), collaboratively developed by our team.

---

## 👥 Team Members

- **Member 1:** Byri Varshini
- **Member 2:** Polusani Ashwanth

---

## 🏆 Challenges Overview

### Challenge 1A: PDF Document Outline Extraction

- **Goal:** Automatically extract a structured outline (title, H1/H2/H3 headings, page numbers) from PDF documents.
- **Tech:** Python, PyMuPDF, JSON serialization.
- **Output:** For each PDF, a JSON file with the document title and a hierarchical outline.

### Challenge 1B: Multi-Collection PDF Intelligence

- **Goal:** Given a persona and a task, intelligently surface the most relevant sections/snippets from a collection of PDFs.
- **Tech:** Python, PyMuPDF, sentence-transformers (MiniLM), scikit-learn.
- **Output:** Ranked JSON results with metadata, relevant sections, and context snippets.

---

## 🗂️ Repository Structure

```
adobe-hackathon-project/
├── Challenge_1a/
│   ├── sample_dataset/
│   ├── process_pdfs.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── Challenge_1b/
│   ├── input/
│   ├── output/
│   ├── main.py
│   ├── Dockerfile
│   └── README.md
└── README.md   ← (You are here)
```

---

## 🐳 Quickstart: Running Both Solutions with Docker

### 1A: PDF Outline Extraction

```bash
cd Challenge_1a
docker build -t challenge1a.processor .
docker run --rm \
  -v ${PWD}/sample_dataset/pdfs:/app/input:ro \
  -v ${PWD}/sample_dataset/outputs:/app/output \
  --network none challenge1a.processor
```

### 1B: Multi-Collection PDF Intelligence

```bash
cd Challenge_1b
docker build -t adobe-challenge-1b .
docker run --rm \
  -v "${PWD}/input:/app/input" \
  -v "${PWD}/output:/app/output" \
  --network none \
  adobe-challenge-1b
```

---

## 📖 How Each Solution Works

### Challenge 1A

- **Extracts**: Title and headings (H1, H2, H3) with page numbers.
- **Method**: Analyzes font size, style, and position using PyMuPDF.
- **Output**: JSON outline per PDF.

### Challenge 1B

- **Extracts**: Most relevant sections/snippets for a given persona and task.
- **Method**: 
  - Detects section titles and context blocks.
  - Embeds text and persona/task using MiniLM.
  - Ranks by cosine similarity and domain keyword boosting.
- **Output**: Ranked JSON with metadata and context.

---

## 📦 Dependencies

- Python 3.10+
- PyMuPDF
- sentence-transformers
- scikit-learn
- (See each challenge's `requirements.txt` or Dockerfile)

---

## 🤝 Acknowledgements

Thanks to Adobe for the opportunity and to all open-source contributors whose tools made this possible!

---

## 📬 Contact

For questions or collaboration, please reach out to ashwanthpolusani@gmail.com