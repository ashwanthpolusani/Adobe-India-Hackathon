import os
import re
import json
import glob
import fitz  # PyMuPDF
import numpy as np
from collections import Counter, defaultdict
from sentence_transformers import SentenceTransformer,util

# --- CONFIGURATION AND CONSTANTS ---

# Define the input and output directories as specified in the Docker environment.
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"
# The chosen sentence-transformer model for semantic analysis.
# This model will be loaded from the local files within the Docker container.
MODEL_NAME = 'all-MiniLM-L6-v2'


# --- CORE PROCESSING LOGIC ---

def get_document_styles(doc):
    """
    Analyzes the document to identify the most common font size, which is
    assumed to be the body text size. This serves as a baseline for identifying
    headings, which typically have a larger font size.

    Args:
        doc: A fitz.Document object.

    Returns:
        A tuple containing the body text size (float) and a dictionary of all
        font sizes found in the document.
    """
    font_counts = Counter()
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0:  # Text block
                for l in b['lines']:
                    for s in l['spans']:
                        font_counts[round(s['size'])] += 1
    
    if not font_counts:
        return 10.0, {} # Default body size if no text is found
        
    body_size = font_counts.most_common(1)[0][0]
    return float(body_size), font_counts.keys()


def extract_text_blocks(doc, body_size):
    """
    Extracts all text blocks from the document, enriching them with metadata.
    It filters out headers, footers, and text smaller than the body size.

    Args:
        doc: A fitz.Document object.
        body_size: The font size of the main body text.

    Returns:
        A list of dictionaries, where each dictionary represents a text block.
    """
    blocks = []
    for page_num, page in enumerate(doc, 1):
        # Filter out common header/footer regions
        page_height = page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b['type'] == 0:
                # Basic header/footer filtering
                y0 = b['bbox'][1]
                if y0 < 50 or y0 > page_height - 50:
                    continue

                for l in b['lines']:
                    for s in l['spans']:
                        text = s['text'].strip()
                        font_size = round(s['size'])
                        
                        # Ignore text that is too small or likely just a page number
                        if text and font_size >= body_size and not text.isdigit():
                            blocks.append({
                                'text': text,
                                'font_size': font_size,
                                'font_name': s['font'],
                                'is_bold': 'bold' in s['font'].lower(),
                                'page': page_num,
                                'bbox': s['bbox'],
                                'processed': False # Flag for the hybrid approach
                            })
    return blocks


def heuristic_pass(blocks, body_size):
    """
    Performs a high-confidence heuristic pass to identify headings based on
    numerical prefixes and font styles.

    Args:
        blocks: A list of text block dictionaries.
        body_size: The font size of the main body text.
    """
    # Regex to find numerical prefixes like "1.", "2.1", "3.1.4"
    numerical_prefix_re = re.compile(r'^\d+(\.\d+)*\s')
    
    for block in blocks:
        if block['processed']:
            continue
        
        match = numerical_prefix_re.match(block['text'])
        # Condition: Has a numerical prefix AND is bold or larger than body text
        if match and (block['is_bold'] or block['font_size'] > body_size):
            level = len(match.group(0).strip().split('.'))
            if level <= 3:
                block['level'] = f"H{level}"
                block['processed'] = True


def semantic_pass(blocks, model):
    """
    Performs a semantic analysis pass on unprocessed blocks using a
    sentence-transformer model to find headings that heuristics missed.

    Args:
        blocks: A list of text block dictionaries.
        model: A loaded SentenceTransformer model.
    """
    unprocessed_texts = [b['text'] for b in blocks if not b['processed']]
    if not unprocessed_texts:
        return

    # Generate embeddings for all unprocessed text blocks at once for efficiency
    embeddings = model.encode(unprocessed_texts, convert_to_tensor=True)

    # Prototype for what a "heading" semantically represents
    # This captures concepts like titles, sections, chapters, introductions
    heading_prototype = model.encode(["title chapter section introduction summary references appendix"])
    
    # Calculate cosine similarity
    similarities = util.cos_sim(embeddings, heading_prototype).cpu().numpy().flatten()

    unprocessed_indices = [i for i, b in enumerate(blocks) if not b['processed']]
    
    # Classify as heading if similarity is above a certain threshold
    # This threshold may need tuning but is a good starting point.
    heading_threshold = 0.4
    for i, sim in zip(unprocessed_indices, similarities):
        if sim > heading_threshold:
            blocks[i]['level'] = 'H_semantic' # Mark as semantically found
            blocks[i]['processed'] = True


def consolidate_and_level(blocks, font_sizes):
    """
    Consolidates all identified headings and assigns final H1, H2, H3 levels.
    This function uses font size as the primary determinant for hierarchy.

    Args:
        blocks: The list of processed text block dictionaries.
        font_sizes: A list of all unique font sizes in the document.

    Returns:
        A tuple containing the document title and the final outline list.
    """
    headings = [b for b in blocks if b.get('level')]
    if not headings:
        return "Unknown Document", []

    # Sort headings by page number and then by vertical position
    headings.sort(key=lambda x: (x['page'], x['bbox'][1]))
    
    # Determine levels based on font size (larger font = higher level)
    heading_font_sizes = sorted([s for s in font_sizes if s in {h['font_size'] for h in headings}], reverse=True)
    
    level_map = {}
    for i, size in enumerate(heading_font_sizes[:3]): # Max H1, H2, H3
        level_map[size] = f"H{i+1}"

    # Assign final levels and identify the title
    final_outline = []
    title = "Unknown Document"
    title_found = False
    
    for h in headings:
        # Heuristically-found levels are more reliable
        if h['level'] in ['H1', 'H2', 'H3']:
            final_level = h['level']
        # Semantically-found levels are determined by font size
        elif h['font_size'] in level_map:
            final_level = level_map[h['font_size']]
        else:
            continue # Skip if it can't be mapped to H1-H3

        # The first H1 is assumed to be the title
        if not title_found and final_level == 'H1':
            title = h['text']
            title_found = True
        else:
            final_outline.append({
                "level": final_level,
                "text": h['text'],
                "page": h['page']
            })
            
    # If no H1 was found for the title, use the first heading overall
    if not title_found and headings:
        title = headings[0]['text']
        # Remove the title from the outline if it was added
        if final_outline and final_outline[0]['text'] == title:
            final_outline.pop(0)

    return title, final_outline


def process_pdfs():
    """
    Main function to orchestrate the PDF processing pipeline.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load the ML model once
    # Note: In a real Docker environment, the model should be pre-downloaded
    # and included in the Docker image to ensure offline operation.
    try:
        from sentence_transformers import util
        model = SentenceTransformer(MODEL_NAME)
        ml_enabled = True
    except ImportError:
        print("SentenceTransformers library not found. Running in heuristics-only mode.")
        model = None
        ml_enabled = False
    except Exception as e:
        print(f"Could not load model {MODEL_NAME}. Running in heuristics-only mode. Error: {e}")
        model = None
        ml_enabled = False

    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {INPUT_DIR}")
        return

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
            
            # Stage 1: Analyze styles and extract all potential text blocks
            body_size, font_sizes = get_document_styles(doc)
            blocks = extract_text_blocks(doc, body_size)
            
            # Stage 2: High-confidence heuristic pass
            heuristic_pass(blocks, body_size)
            
            # Stage 3: Semantic pass for remaining candidates (if model is available)
            if ml_enabled:
                semantic_pass(blocks, model)

            # Stage 4: Consolidate results and assign final levels
            title, outline = consolidate_and_level(blocks, font_sizes)
            
            # Final JSON Output
            output_data = {"title": title, "outline": outline}
            output_filename = os.path.join(OUTPUT_DIR, f"{os.path.splitext(os.path.basename(pdf_path))[0]}.json")
            
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
                
            print(f"Successfully created: {output_filename}")

        except Exception as e:
            print(f"Failed to process {pdf_path}. Error: {e}")


# --- SCRIPT EXECUTION ---

if __name__ == "__main__":
    # This check allows the script to be imported without running the main function.
    process_pdfs()
