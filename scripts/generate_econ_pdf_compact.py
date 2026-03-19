import os
import re
from fpdf import FPDF
from PIL import Image
from mansur_bot.config import UNIVERSITY_DIR

ECON_DIR = UNIVERSITY_DIR / "Economics"
EXAM_PREP_FILE = os.fspath(ECON_DIR / "Exam_Prep.md")
ECON_IMAGES_DIR = os.fspath(ECON_DIR)
OUTPUT_PDF = os.fspath(ECON_DIR / "Economics_Assignments_Compact.pdf")

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 8, 'Economics Assignments & Solutions (Compact)', 0, 1, 'C')
        self.ln(2)

    def footer(self):
        self.set_y(-10)
        self.set_font('helvetica', 'I', 7)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    if not os.path.exists(EXAM_PREP_FILE):
        print("❌ Exam_Prep.md not found!")
        return

    with open(EXAM_PREP_FILE, 'r') as f:
        content = f.read()

    assignments = re.split(r'(?m)^## Assignment\s+', content)
    
    for a_num, assignment in enumerate(assignments[1:], 1):
        # Very compact Assignment Header
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 6, f"ASSIGNMENT {a_num}", 1, 1, 'L', fill=True)
        
        questions = re.split(r'(?m)^### Question\s+', assignment)
        
        for q_num, question_text in enumerate(questions[1:], 1):
            lines = question_text.strip().split('\n')
            header = lines[0]
            body = '\n'.join(lines[1:])
            
            # Compact Question Header
            pdf.ln(1)
            pdf.set_font('helvetica', 'B', 9)
            clean_header = header.encode('latin-1', 'ignore').decode('latin-1')
            pdf.cell(0, 5, f"Q{q_num}: {clean_header}", 0, 1, 'L')
            
            # Check for image - set much smaller max height for compactness
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
                        img = Image.open(img_file)
                        w, h = img.size
                        aspect = h / w
                        # Target small height for thumbnails
                        pdf_h = 35 
                        pdf_w = pdf_h / aspect
                        
                        # If it gets too wide, cap it
                        if pdf_w > 80:
                            pdf_w = 80
                            pdf_h = pdf_w * aspect
                            
                        pdf.image(img_file, x=15, w=pdf_w)
                        pdf.ln(1)
                    except Exception:
                        pass # Skip broken images to save space

            # Split body into components
            parts = re.split(r'(\*\*Correct Answer:\*\*|\*\*Explanation:\*\*)', body)
            
            for part in parts:
                p = part.strip()
                if not p: continue
                
                if p == "**Correct Answer:**":
                    pdf.set_font('helvetica', 'B', 9)
                    pdf.set_text_color(0, 100, 0)
                    pdf.write(4, " Ans: ")
                elif p == "**Explanation:**":
                    pdf.set_font('helvetica', 'B', 9)
                    pdf.set_text_color(100, 0, 0)
                    pdf.write(4, " | Expl: ")
                else:
                    pdf.set_font('helvetica', '', 8.5)
                    pdf.set_text_color(0, 0, 0)
                    # Clean special chars
                    clean_text = p.replace('**', '').replace('###', '')
                    clean_text = clean_text.replace('\u2022', '- ').replace('\u2013', '-').replace('\u2014', '-')
                    clean_text = clean_text.replace('\u201d', '"').replace('\u201c', '"').replace('\u2019', "'").replace('\u2018', "'")
                    clean_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
                    
                    # If it's the answer choice (single letter), stay on same line
                    if len(clean_text.strip()) <= 2:
                        pdf.write(4, clean_text.strip())
                    else:
                        pdf.ln(4)
                        pdf.multi_cell(0, 3.5, clean_text)
            
            pdf.ln(2)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(1)

    pdf.output(OUTPUT_PDF)
    print(f"✅ Compact PDF created: {OUTPUT_PDF}")

if __name__ == "__main__":
    create_pdf()
