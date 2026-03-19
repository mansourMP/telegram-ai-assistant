import os
import re
from fpdf import FPDF
from PIL import Image
from mansur_bot.config import UNIVERSITY_DIR

ECON_DIR = UNIVERSITY_DIR / "Economics"
EXAM_PREP_FILE = os.fspath(ECON_DIR / "Exam_Prep.md")
ECON_IMAGES_DIR = os.fspath(ECON_DIR)
OUTPUT_PDF = os.fspath(ECON_DIR / "Economics_Graph_Gallery_8up.pdf")

class GalleryPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.col = 0 
        self.row = 0 
        self.set_auto_page_break(False)
        # 2 columns x 4 rows = 8 per page
        self.q_w = 105
        self.q_h = 74.25 # 297 / 4

    def start_cell(self, label):
        self.x_off = self.col * self.q_w
        self.y_off = self.row * self.q_h
        
        # Quadrant border
        self.set_draw_color(200, 200, 200)
        self.rect(self.x_off, self.y_off, self.q_w, self.q_h)
        
        self.set_xy(self.x_off + 3, self.y_off + 2)
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(0, 50, 150)
        self.cell(0, 4, label, align='L')
        self.set_text_color(0, 0, 0)
        return self.x_off + 3, self.y_off + 6

    def next_cell(self):
        self.col += 1
        if self.col > 1:
            self.col = 0
            self.row += 1
        if self.row > 3:
            self.row = 0
            self.col = 0
            self.add_page()
        # No need to return anything, start_cell handles the rest

def generate_gallery():
    pdf = GalleryPDF()
    pdf.add_page()
    
    if not os.path.exists(EXAM_PREP_FILE):
        print("❌ File not found")
        return

    with open(EXAM_PREP_FILE, 'r') as f:
        content = f.read()

    assignments = re.split(r'(?m)^## Assignment\s+', content)
    
    found_any = False
    for a_idx, assignment in enumerate(assignments[1:], 1):
        questions = re.split(r'(?m)^### Question\s+', assignment)
        
        for q_idx, q_text in enumerate(questions[1:], 1):
            lines = q_text.strip().split('\n')
            header = lines[0]
            body = '\n'.join(lines[1:])
            
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
                    if found_any:
                        pdf.next_cell()
                    found_any = True
                    
                    x, y = pdf.start_cell(f"A{a_idx}-Q{q_idx} (IMG_{img_num})")
                    
                    # 1. Place Image
                    try:
                        img = Image.open(img_file)
                        w, h = img.size
                        aspect = h / w
                        pdf_w = 95
                        pdf_h = pdf_w * aspect
                        
                        # In 8-up, height is tight (max ~45mm for image)
                        if pdf_h > 45:
                            pdf_h = 45
                            pdf_w = pdf_h / aspect
                            
                        pdf.image(img_file, x=x, y=y, w=pdf_w)
                        y_next = y + pdf_h + 1
                    except Exception:
                        y_next = y + 5
                    
                    # 2. Place Question Snippet & Answer
                    pdf.set_xy(x, y_next)
                    
                    # Extract Answer
                    ans_match = re.search(r'\*\*Correct Answer:\*\*\s*(.+)', body)
                    answer = ans_match.group(1).strip() if ans_match else "?"
                    
                    # Question text (truncated)
                    q_text_clean = body.split('**Correct Answer:**')[0].strip()
                    q_text_clean = q_text_clean.replace('**', '').replace('\n', ' ')
                    q_text_clean = q_text_clean.encode('latin-1', 'ignore').decode('latin-1')
                    if len(q_text_clean) > 80:
                        q_text_clean = q_text_clean[:77] + "..."
                    
                    pdf.set_font('helvetica', '', 7)
                    pdf.multi_cell(95, 3, q_text_clean)
                    
                    pdf.set_font('helvetica', 'B', 8)
                    pdf.set_text_color(0, 120, 0)
                    pdf.cell(0, 5, f"Correct Answer: {answer}")
                    pdf.set_text_color(0, 0, 0)

    pdf.output(OUTPUT_PDF)
    print(f"✅ Image Gallery PDF (8-up) created: {OUTPUT_PDF}")

if __name__ == "__main__":
    generate_gallery()
