import os
import json
import fitz  
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime


def extract_pdf_pages_text(pdf_path):
    doc = fitz.open(pdf_path)
    page_texts = []
    for page in doc:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda blk: (-blk[3] + blk[1]))  # top to bottom
        text_content = "\n".join(block[4] for block in blocks if block[4].strip())
        page_texts.append(text_content)
    return page_texts


def is_likely_heading(line_text):
    line_text = line_text.strip()
    if not line_text or len(line_text.split()) < 3 or len(line_text.split()) > 20:
        return False
    if re.fullmatch(r"[^\w\s]+", line_text):  # only symbols
        return False
    if line_text.isupper() or line_text.istitle():
        return True
    return False


def identify_sections_from_pages(page_texts):
    detected_sections = []
    for page_index, page_content in enumerate(page_texts):
        lines = page_content.split('\n')
        for line in lines:
            if is_likely_heading(line):
                detected_sections.append({
                    "section_title": line.strip(),
                    "page_number": page_index + 1,
                    "refined_text": None
                })
    return detected_sections


def enrich_sections_with_context(page_texts, section_list):
    enriched_sections = []
    for section in section_list:
        current_page_text = page_texts[section["page_number"] - 1]
        paragraph = ""
        lines = current_page_text.split('\n')
        found_heading = False
        for i, line in enumerate(lines):
            if section["section_title"] in line:
                found_heading = True
                paragraph = "\n".join(lines[i:i + 15])
                break
        if not found_heading:
            paragraph = current_page_text[:1000]
        enriched_sections.append({**section, "refined_text": paragraph})
    return enriched_sections


def rank_sections_by_relevance(section_entries, user_query, embedding_model):
    if not section_entries:
        return []

    relevance_keywords = [
        "packing", "cuisine", "food", "activities", "things to do",
        "entertainment", "nightlife", "tips", "tricks", "guide",
        "plan", "water sports", "coastal", "restaurants", "cities",
        "checklist", "hotel", "transport", "local"
    ]

    section_texts = []
    section_boosts = []

    for entry in section_entries:
        combined_text = entry["section_title"] + " " + (entry["refined_text"] or "")
        section_texts.append(combined_text)

        if any(keyword in combined_text.lower() for keyword in relevance_keywords):
            section_boosts.append(0.1)
        else:
            section_boosts.append(0.0)

    section_embeddings = embedding_model.encode(section_texts)
    query_embedding = embedding_model.encode([user_query])
    similarity_scores = cosine_similarity(query_embedding, section_embeddings)[0]
    final_scores = [score + boost for score, boost in zip(similarity_scores, section_boosts)]

    ranked_sections = sorted(zip(section_entries, final_scores), key=lambda x: -x[1])

    return [dict(entry[0], importance_rank=index + 1) for index, entry in enumerate(ranked_sections)]


def process_all_pdfs(input_folder, user_persona, user_task):
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    compiled_sections = []
    document_list = []

    for file in os.listdir(input_folder):
        if file.endswith(".pdf"):
            file_path = os.path.join(input_folder, file)
            page_contents = extract_pdf_pages_text(file_path)
            raw_sections = identify_sections_from_pages(page_contents)
            enriched_sections = enrich_sections_with_context(page_contents, raw_sections)
            for section in enriched_sections:
                section["document"] = file
            compiled_sections.extend(enriched_sections)
            document_list.append(file)

    combined_query = f"{user_persona} - {user_task}"
    ranked_output_sections = rank_sections_by_relevance(compiled_sections, combined_query, embedding_model)

    final_output = {
        "metadata": {
            "input_documents": document_list,
            "persona": user_persona,
            "job_to_be_done": user_task,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": [
            {
                "document": s["document"],
                "section_title": s["section_title"],
                "importance_rank": s["importance_rank"],
                "page_number": s["page_number"]
            }
            for s in ranked_output_sections
        ],
        "subsection_analysis": [
            {
                "document": s["document"],
                "refined_text": s["refined_text"].replace("\n", " ").strip(),
                "page_number": s["page_number"]
            }
            for s in ranked_output_sections
        ]
    }

    return final_output


if __name__ == "__main__":
    input_folder = "./input"
    output_folder = "./output"
    output_file = os.path.join(output_folder, "travel_planner.json")

    user_persona = "Travel Planner"
    user_task = "Plan a trip of 4 days for a group of 10 college friends."

    os.makedirs(output_folder, exist_ok=True)
    analysis_result = process_all_pdfs(input_folder, user_persona, user_task)

    with open(output_file, "w", encoding="utf-8") as output_json:
        json.dump(analysis_result, output_json, indent=4, ensure_ascii=False)

    print(f"Output written to {output_file}")
