import os
import re
import io
from fpdf import FPDF
from PIL import Image
from mansur_bot.config import UNIVERSITY_DIR

ECON_DIR = UNIVERSITY_DIR / "Economics"
EXAM_PREP_FILE = os.fspath(ECON_DIR / "Exam_Prep.md")
ECON_IMAGES_DIR = os.fspath(ECON_DIR)
OUTPUT_PDF = os.fspath(ECON_DIR / "Economics_Full_8up.pdf")

class Full8upPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.col = 0 
        self.row = 0 
        self.set_auto_page_break(False)
        self.q_w = 105
        self.q_h = 74.25

    def start_cell(self, label):
        self.x_off = self.col * self.q_w
        self.y_off = self.row * self.q_h
        self.set_left_margin(self.x_off + 4)
        self.set_right_margin(210 - (self.x_off + 101))
        self.set_draw_color(180, 180, 180)
        self.rect(self.x_off, self.y_off, self.q_w, self.q_h)
        self.set_xy(self.x_off + 4, self.y_off + 3)
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(0, 50, 150)
        self.cell(0, 4, label, align='L', new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def next_cell(self):
        self.col += 1
        if self.col > 1:
            self.col = 0
            self.row += 1
        if self.row > 3:
            self.row = 0
            self.col = 0
            self.add_page()

def generate_full_8up():
    pdf = Full8upPDF()
    pdf.add_page()
    
    if not os.path.exists(EXAM_PREP_FILE):
        return

    with open(EXAM_PREP_FILE, 'r') as f:
        content = f.read()

    assignments = re.split(r'(?m)^## Assignment\s+', content)
    
    q_count = 0
    for a_idx, assignment in enumerate(assignments[1:], 1):
        questions = re.split(r'(?m)^### Question\s+', assignment)
        for q_idx, q_text in enumerate(questions[1:], 1):
            if q_count > 0:
                pdf.next_cell()
            q_count += 1
            
            pdf.start_cell(f"A{a_idx}-Q{q_idx}")
            
            sections = re.split(r'(```.*?```)', q_text, flags=re.DOTALL)
            
            for section in sections:
                if section.startswith('```'):
                    code_content = section.strip('`').strip()
                    code_content = code_content.replace('\u2022', '-').replace('\u2013', '-').replace('\u2014', '-')
                    code_content = code_content.encode('latin-1', 'ignore').decode('latin-1')
                    pdf.set_font('courier', '', 6)
                    pdf.set_text_color(50, 50, 50)
                    for c_line in code_content.split('\n'):
                        if pdf.get_y() > (pdf.y_off + 72): break
                        pdf.cell(0, 2.5, c_line, new_x="LMARGIN", new_y="NEXT")
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(1)
                    continue

                # Normal text processing
                img_nums = re.findall(r'IMG_(\d+)', section)
                for img_num in img_nums:
                    img_file = ""
                    for ext in ['.jpg', '.jpeg', '.png', '.PNG', '.JPG', '.JPEG']:
                        path = os.path.join(ECON_IMAGES_DIR, f"IMG_{img_num}{ext}")
                        if os.path.exists(path):
                            img_file = path
                            break
                    if img_file:
                        try:
                            # ROTATE 90 DEGREES (Sleeping Style)
                            img = Image.open(img_file)
                            img_rotated = img.rotate(90, expand=True)
                            
                            # Save to memory buffer for FPDF
                            img_byte_arr = io.BytesIO()
                            img_rotated.save(img_byte_arr, format='PNG')
                            img_byte_arr.seek(0)
                            
                            w, h = img_rotated.size
                            aspect = h / w
                            
                            # Now that it's rotated, it can be much taller/wider
                            pdf_w = 95 # Fill the width of the quadrant
                            pdf_h = pdf_w * aspect
                            
                            # Cap height so we don't take the whole quadrant vertically
                            if pdf_h > 45: 
                                pdf_h = 45
                                pdf_w = pdf_h / aspect
                            
                            if pdf.get_y() + pdf_h < (pdf.y_off + 72):
                                pdf.image(img_byte_arr, x=pdf.get_x(), w=pdf_w)
                                pdf.set_y(pdf.get_y() + pdf_h + 1)
                        except Exception as e:
                            print(f"Error processing IMG_{img_num}: {e}")

                sub_parts = re.split(r'(\*\*Correct Answer:\*\*|\*\*Explanation:\*\*)', section)
                for sp in sub_parts:
                    p = sp.strip()
                    if not p: continue
                    if pdf.get_y() > (pdf.y_off + 71): break
                    
                    if p == "**Correct Answer:**":
                        pdf.set_font('helvetica', 'B', 7)
                        pdf.set_text_color(0, 100, 0)
                        pdf.write(3, " Ans: ")
                    elif p == "**Explanation:**":
                        pdf.set_font('helvetica', 'B', 7)
                        pdf.set_text_color(150, 0, 0)
                        pdf.write(3, " | Expl: ")
                    else:
                        pdf.set_font('helvetica', '', 6.5)
                        pdf.set_text_color(0, 0, 0)
                        clean = p.replace('**', '').replace('###', '')
                        clean = clean.encode('latin-1', 'ignore').decode('latin-1')
                        
                        if len(clean) <= 3:
                            pdf.write(3, clean)
                        else:
                            pdf.ln(3)
                            lines = pdf.multi_cell(0, 2.5, clean, dry_run=True, output="LINES")
                            for line in lines:
                                if pdf.get_y() > (pdf.y_off + 72): break
                                pdf.cell(0, 2.5, line, new_x="LMARGIN", new_y="NEXT")

    pdf.output(OUTPUT_PDF)
    print(f"✅ Full 8-up (Rotated Sleeping Images) created: {OUTPUT_PDF}")

if __name__ == "__main__":
    generate_full_8up()
