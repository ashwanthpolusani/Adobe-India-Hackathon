
# **Adobe Hackathon Challenge 1B – Multi-Collection PDF Intelligence**

## 🚀 Overview

This project solves **Challenge 1B** of the Adobe India Hackathon, where the objective is to build an intelligent system that analyzes a collection of PDF documents and surfaces the most relevant information based on a given **persona** and their **specific task**.

**Example Use Case**  
- **Persona**: Travel Planner  
- **Goal**: Design a 4-day itinerary for a group of 10 college friends  

The system ranks and returns the most meaningful document sections and context snippets that help the persona accomplish their task with clarity and speed.

---

## 🧠 Approach Summary

### 1. 📄 PDF Text Extraction  
Utilizes `PyMuPDF (fitz)` to parse PDF content page-by-page. Text blocks are sorted in visual reading order (top-down) to maintain logical flow.

### 2. 🧩 Section Title Detection  
A custom function identifies likely section headers using rules like:
- Between 3 and 20 words  
- Must be Title Case or ALL CAPS  
- Excludes noise like numeric values or symbols  
This ensures that only semantically meaningful headings are considered.

### 3. 🧵 Contextual Block Retrieval  
For each detected section, a surrounding context block (approx. 15 lines) is extracted from the same page. If no headings are found, a fallback snippet (e.g., first 1000 characters) is used to preserve insight coverage.

### 4. 🧠 Relevance Scoring & Ranking  
- Embeddings are generated using `all-MiniLM-L6-v2` from `sentence-transformers`  
- Both the (section + context) and the (persona + task) are embedded  
- Cosine similarity is calculated to score relevance  
- Boosting is applied for keywords aligned with the domain (e.g., "activities", "local", "cuisine", "guide", etc.)

### 5. 🧾 Output Format  
Results are structured in JSON, including:
- **Metadata**: persona, task, timestamp, file list  
- **Extracted Sections**: document name, section title, page number, relevance score  
- **Subsection Analysis**: document name, refined snippet, page number  

---

## 🐳 Docker Setup

### Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir \
    PyMuPDF \
    sentence-transformers \
    scikit-learn

CMD ["python", "main.py"]
````

---

## 🗂️ Folder Structure

```
project_folder/
├── input/              # Input PDFs (e.g., itinerary.pdf, travelguide.pdf)
├── output/             # Generated output JSONs
├── main.py             # Main processing logic
├── Dockerfile          # Container build definition
```

---

## 🛠️ How to Build the Docker Image

From the project directory, run:

```bash
docker build -t adobe-challenge-1b .
```

---

## 🚀 How to Execute

Ensure your PDFs are placed in the `input/` folder, then run:

```bash
docker run --rm \
  -v "/$PWD/input:/app/input" \
  -v "/$PWD/output:/app/output" \
  --network none \
  adobe-challenge-1b
```

