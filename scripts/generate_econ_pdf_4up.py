import os
import re
from fpdf import FPDF
from PIL import Image
from mansur_bot.config import UNIVERSITY_DIR

ECON_DIR = UNIVERSITY_DIR / "Economics"
EXAM_PREP_FILE = os.fspath(ECON_DIR / "Exam_Prep.md")
ECON_IMAGES_DIR = os.fspath(ECON_DIR)
OUTPUT_PDF = os.fspath(ECON_DIR / "Economics_Assignments_4up.pdf")

class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.col = 0 
        self.row = 0 
        self.set_auto_page_break(False)
        # Quadrant dimensions for A4 (210x297)
        self.q_w = 105
        self.q_h = 148.5

    def start_quadrant(self):
        self.x_offset = self.col * self.q_w
        self.y_offset = self.row * self.q_h
        
        # CRITICAL: Set margins to the quadrant boundaries so multi_cell wraps correctly
        self.set_left_margin(self.x_offset + 5)
        self.set_right_margin(210 - (self.x_offset + 100)) # 105 - 5 margin = 100
        
        # Reset position to top-left of quadrant
        self.set_xy(self.x_offset + 5, self.y_offset + 5)
        
        # Draw the quadrant border
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.2)
        self.rect(self.x_offset, self.y_offset, self.q_w, self.q_h)
        
        # Page info
        self.set_font('helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(95, 5, f'Sheet {self.page_no()} | Quad {self.row*2 + self.col + 1}', align='R', new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def next_quadrant(self):
        self.col += 1
        if self.col > 1:
            self.col = 0
            self.row += 1
        if self.row > 1:
            self.row = 0
            self.col = 0
            self.add_page()
        self.start_quadrant()

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    pdf.start_quadrant()
    
    if not os.path.exists(EXAM_PREP_FILE):
        print("❌ Exam_Prep.md not found!")
        return

    with open(EXAM_PREP_FILE, 'r') as f:
        content = f.read()

    assignments = re.split(r'(?m)^## Assignment\s+', content)
    
    q_count = 0
    for a_idx, assignment in enumerate(assignments[1:], 1):
        questions = re.split(r'(?m)^### Question\s+', assignment)
        
        for q_idx, q_text in enumerate(questions[1:], 1):
            if q_count > 0:
                pdf.next_quadrant()
            q_count += 1

            lines = q_text.strip().split('\n')
            header = lines[0]
            body = '\n'.join(lines[1:])
            
            # Header Info
            pdf.set_font('helvetica', 'B', 10)
            pdf.set_text_color(0, 50, 150)
            pdf.cell(0, 6, f"Assignment {a_idx} - Q{q_idx}", align='L', new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            
            # Question Title
            pdf.set_font('helvetica', 'B', 9)
            clean_header = header.encode('latin-1', 'ignore').decode('latin-1')
            pdf.multi_cell(0, 4, clean_header)
            pdf.ln(1)
            
            # Handle Image
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
                        pdf_w = 90 # Max width for quadrant
                        pdf_h = pdf_w * aspect
                        
                        # Cap image height to leave room for text
                        if pdf_h > 70:
                            pdf_h = 70
                            pdf_w = pdf_h / aspect
                            
                        pdf.image(img_file, x=pdf.get_x(), w=pdf_w)
                        pdf.set_y(pdf.get_y() + pdf_h + 2)
                    except Exception:
                        pass

            # Body Text (Answer & Explanation)
            parts = re.split(r'(\*\*Correct Answer:\*\*|\*\*Explanation:\*\*)', body)
            for part in parts:
                p = part.strip()
                if not p: continue
                
                # Check vertical bounds to prevent overlap into next quadrant
                if pdf.get_y() > (pdf.y_offset + 140):
                    break # Stop writing if we hit the bottom
                
                if p == "**Correct Answer:**":
                    pdf.set_font('helvetica', 'B', 9)
                    pdf.set_text_color(0, 120, 0)
                    pdf.write(4, "Correct Answer: ")
                elif p == "**Explanation:**":
                    pdf.ln(5)
                    pdf.set_font('helvetica', 'B', 8)
                    pdf.set_text_color(150, 0, 0)
                    pdf.write(4, "Explanation: ")
                else:
                    pdf.set_font('helvetica', '', 8.5)
                    pdf.set_text_color(0, 0, 0)
                    clean_text = p.replace('**', '').replace('###', '')
                    clean_text = clean_text.replace('\u2022', '- ').replace('\u201d', '"').replace('\u201c', '"')
                    clean_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
                    
                    if len(clean_text.strip()) <= 3:
                        pdf.write(4, clean_text.strip())
                    else:
                        pdf.ln(4)
                        # Multi-cell with 0 width will follow quadrant margins
                        pdf.multi_cell(0, 3.5, clean_text)

    pdf.output(OUTPUT_PDF)
    print(f"✅ Corrected 4-up Grid PDF created: {OUTPUT_PDF}")

if __name__ == "__main__":
    create_pdf()
