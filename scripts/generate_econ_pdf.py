import os
import re
from fpdf import FPDF
from PIL import Image
from mansur_bot.config import UNIVERSITY_DIR

ECON_DIR = UNIVERSITY_DIR / "Economics"
EXAM_PREP_FILE = os.fspath(ECON_DIR / "Exam_Prep.md")
ECON_IMAGES_DIR = os.fspath(ECON_DIR)
OUTPUT_PDF = os.fspath(ECON_DIR / "Economics_Assignments.pdf")

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Economics Assignments & Solutions', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    if not os.path.exists(EXAM_PREP_FILE):
        print("❌ Exam_Prep.md not found!")
        return

    with open(EXAM_PREP_FILE, 'r') as f:
        content = f.read()

    # Split by Assignments
    assignments = re.split(r'(?m)^## Assignment\s+', content)
    
    for a_num, assignment in enumerate(assignments[1:], 1):
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(0, 51, 102) # Dark blue for assignment headers
        pdf.cell(0, 10, f"Assignment {a_num}", 0, 1, 'L')
        pdf.set_text_color(0, 0, 0) # Back to black
        
        # Split by Questions
        questions = re.split(r'(?m)^### Question\s+', assignment)
        
        for q_num, question_text in enumerate(questions[1:], 1):
            lines = question_text.strip().split('\n')
            header = lines[0]
            body = '\n'.join(lines[1:])
            
            # Question Header
            pdf.ln(5)
            pdf.set_font('helvetica', 'B', 12)
            clean_header = header.encode('latin-1', 'ignore').decode('latin-1')
            pdf.cell(0, 10, f"Question {q_num}: {clean_header}", 0, 1, 'L')
            
            # Check for image
            img_match = re.search(r'\(IMG_(\d+)\)', header)
            if img_match:
                img_num = img_match.group(1)
                img_file = ""
                for ext in ['.jpg', '.jpeg', '.png', '.PNG', '.JPG']:
                    path = os.path.join(ECON_IMAGES_DIR, f"IMG_{img_num}{ext}")
                    if os.path.exists(path):
                        img_file = path
                        break
                
                if img_file:
                    try:
                        # Add image to PDF
                        # Scale to fit width (max 180mm)
                        img = Image.open(img_file)
                        w, h = img.size
                        aspect = h / w
                        pdf_w = 180
                        pdf_h = pdf_w * aspect
                        
                        # If height is too big, scale down
                        if pdf_h > 150:
                            pdf_h = 150
                            pdf_w = pdf_h / aspect
                            
                        pdf.image(img_file, x=15, w=pdf_w)
                        pdf.ln(2)
                    except Exception as e:
                        pdf.set_font('helvetica', 'I', 10)
                        pdf.cell(0, 10, f"[Image load error: {e}]", 0, 1, 'L')
            
            # Question Body
            pdf.set_font('helvetica', '', 11)
            
            # Identify parts: Question text, Answer, Explanation
            parts = re.split(r'(\*\*Correct Answer:\*\*|\*\*Explanation:\*\*)', body)
            
            for part in parts:
                p = part.strip()
                if not p: continue
                
                if p == "**Correct Answer:**":
                    pdf.set_font('helvetica', 'B', 11)
                    pdf.set_text_color(0, 128, 0) # Green for answer label
                    pdf.write(5, "Correct Answer: ")
                    pdf.set_text_color(0, 0, 0)
                elif p == "**Explanation:**":
                    pdf.ln(5)
                    pdf.set_font('helvetica', 'B', 11)
                    pdf.set_text_color(128, 0, 0) # Red for explanation label
                    pdf.write(5, "Explanation: ")
                    pdf.set_text_color(0, 0, 0)
                else:
                    # Content
                    pdf.set_font('helvetica', '', 11)
                    # Simple markdown removal and character cleaning for standard fonts
                    clean_text = p.replace('**', '').replace('###', '')
                    clean_text = clean_text.replace('\u2022', '- ') # bullet
                    clean_text = clean_text.replace('\u2013', '-') # en dash
                    clean_text = clean_text.replace('\u2014', '-') # em dash
                    clean_text = clean_text.replace('\u201d', '"').replace('\u201c', '"') # smart quotes
                    clean_text = clean_text.replace('\u2019', "'").replace('\u2018', "'")
                    # Final safety check for any other non-latin1 chars
                    clean_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
                    
                    pdf.multi_cell(0, 5, clean_text)
                    if p != parts[-1]: pdf.ln(2)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # separator line
            pdf.ln(5)

    pdf.output(OUTPUT_PDF)
    print(f"✅ PDF created: {OUTPUT_PDF}")

if __name__ == "__main__":
    create_pdf()
