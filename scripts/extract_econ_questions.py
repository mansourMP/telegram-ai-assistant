import re
from pathlib import Path

from mansur_bot.config import UNIVERSITY_DIR

ECON_DIR = UNIVERSITY_DIR / "Economics"
EXAM_PREP_FILE = ECON_DIR / "Exam_Prep.md"
ECON_IMAGES_DIR = ECON_DIR

def extract_all_questions():
    if not EXAM_PREP_FILE.exists():
        print("❌ File not found")
        return
    
    with EXAM_PREP_FILE.open('r') as f:
        content = f.read()
    
    # Split content by ### Question
    parts = re.split(r'(?m)^### Question\s+', content)
    
    print(f"--- TOTAL QUESTIONS: {len(parts)-1} ---")
    
    for i, part in enumerate(parts[1:], 1):
        lines = part.strip().split('\n')
        header = lines[0]
        body = '\n'.join(lines[1:])
        
        # Look for images in header like (IMG_XXXX)
        img_match = re.search(r'\(IMG_(\d+)\)', header)
        img_info = ""
        if img_match:
            img_num = img_match.group(1)
            # Find the actual image extension in the directory
            img_filename = ""
            for ext in ['.jpg', '.jpeg', '.png', '.PNG', '.JPG']:
                temp_name = f"IMG_{img_num}{ext}"
                if (ECON_IMAGES_DIR / temp_name).exists():
                    img_filename = temp_name
                    break
            
            if img_filename:
                img_info = f" [Image: {img_filename}]"
            else:
                img_info = f" [Image: {img_num} (File not found!)]"
        
        # Extract Answer
        ans_match = re.search(r'\*\*Correct Answer:\*\*\s*(.+)', body)
        answer = ans_match.group(1).strip() if ans_match else "Not found"
        
        # Extract Question text (briefly)
        q_text = body.split('**Correct Answer:**')[0].strip()
        # Truncate long question texts for summary
        summary_q = (q_text[:100] + '...') if len(q_text) > 100 else q_text
        
        print(f"{i}. {header.strip()}{img_info}")
        print(f"   Q: {summary_q}")
        print(f"   A: {answer}")
        print("-" * 20)

if __name__ == "__main__":
    extract_all_questions()
