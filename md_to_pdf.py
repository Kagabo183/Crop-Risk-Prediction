#!/usr/bin/env python3
"""
Convert markdown documentation to PDF using fpdf2
"""
from fpdf import FPDF
from pathlib import Path
import re

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(44, 95, 45)
        self.cell(0, 10, 'Crop Risk Prediction Platform - Documentation', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title, level=1):
        if level == 1:
            self.set_font('Arial', 'B', 18)
            self.set_text_color(44, 95, 45)
            self.ln(5)
            self.multi_cell(0, 10, title)
            self.ln(3)
        elif level == 2:
            self.set_font('Arial', 'B', 14)
            self.set_text_color(58, 122, 60)
            self.ln(3)
            self.multi_cell(0, 8, title)
            self.ln(2)
        elif level == 3:
            self.set_font('Arial', 'B', 12)
            self.set_text_color(74, 138, 76)
            self.ln(2)
            self.multi_cell(0, 7, title)
            self.ln(1)
        else:
            self.set_font('Arial', 'B', 11)
            self.set_text_color(90, 154, 92)
            self.multi_cell(0, 6, title)
            self.ln(1)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5, body)
        self.ln(2)
    
    def code_block(self, code):
        self.set_fill_color(248, 248, 248)
        self.set_font('Courier', '', 9)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 4, code, 0, 'L', True)
        self.ln(2)
    
    def bullet_point(self, text):
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 51, 51)
        self.cell(10, 5, '-')
        self.multi_cell(0, 5, text)

def parse_markdown_to_pdf(md_file, pdf_file):
    """Parse markdown and create PDF"""
    md_path = Path(md_file)
    if not md_path.exists():
        print(f"Error: {md_file} not found")
        return False
    
    content = md_path.read_text(encoding='utf-8')
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    lines = content.split('\n')
    in_code_block = False
    code_buffer = []
    
    for line in lines:
        # Code blocks
        if line.startswith('```'):
            if in_code_block:
                # End code block
                pdf.code_block('\n'.join(code_buffer))
                code_buffer = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            continue
        
        if in_code_block:
            code_buffer.append(line)
            continue
        
        # Skip empty lines
        if not line.strip():
            continue
        
        # Headers
        if line.startswith('# '):
            pdf.chapter_title(line[2:], 1)
        elif line.startswith('## '):
            pdf.chapter_title(line[3:], 2)
        elif line.startswith('### '):
            pdf.chapter_title(line[4:], 3)
        elif line.startswith('#### '):
            pdf.chapter_title(line[5:], 4)
        # Bullet points
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:]
            # Remove markdown formatting
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
            text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
            text = re.sub(r'`(.*?)`', r'\1', text)        # Code
            text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
            pdf.bullet_point(text)
        # Regular text
        else:
            text = line
            # Remove markdown formatting
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            text = re.sub(r'`(.*?)`', r'\1', text)
            text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
            
            if text.strip():
                pdf.chapter_body(text)
    
    # Save PDF
    try:
        pdf.output(pdf_file)
        print(f"✓ PDF successfully created: {pdf_file}")
        print(f"  File size: {Path(pdf_file).stat().st_size / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False

if __name__ == "__main__":
    md_file = "COMPLETE_PROJECT_DOCUMENTATION.md"
    pdf_file = "COMPLETE_PROJECT_DOCUMENTATION.pdf"
    
    print("Converting markdown to PDF...")
    parse_markdown_to_pdf(md_file, pdf_file)
