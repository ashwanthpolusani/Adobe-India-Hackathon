# **Adobe Hackathon Challenge 1A - PDF Document Outline Extraction**
## 🚀 Overview

This solution addresses **Challenge 1A** of the Adobe India Hackathon, where the objective is to convert PDF documents into structured outlines. The extracted hierarchy includes:

- **Document Title**
- **Headings**: H1, H2, H3
- **Associated Page Numbers**
The resulting outline enables smarter downstream applications like semantic search, document navigation, and insight extraction.

## 📁 Folder Structure

```bash
CHALLENGE-1A/
├── sample_dataset/
│   ├── pdfs/                   # Input PDFs
│   ├── outputs/                # Generated output JSONs
│   └── schema/
│       └── output_schema.json  # Output structure specification
├── process_pdfs.py             # Core extraction script
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
````

---

## 🧾 Output Format

Each PDF is converted into a `.json` file matching the schema:

```json
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
```

You can find the schema at:

```
sample_dataset/schema/output_schema.json
```


## 🧠 How It Works

1. **PDF Parsing**

   * Uses `PyMuPDF` to extract raw text along with font sizes, positions, and styles.

2. **Title & Heading Detection**

   * Title is inferred as the largest, top-most prominent text block.
   * Headings (H1, H2, H3) are classified based on:

     * Font size
     * Text formatting
     * Capitalization
     * Positional hierarchy

3. **Structured Output**

   * Results are serialized into well-formatted JSON files for each input PDF.

---

## 🐳 Docker Usage

### 🧱 Build the Image

```bash
docker build -t challenge1a.processor .
```

### 🚀 Run the Processor

```bash
docker run --rm \
  -v ${PWD}/sample_dataset/pdfs:/app/input:ro \
  -v ${PWD}/sample_dataset/outputs:/app/output \
  --network none challenge1a.processor
```


