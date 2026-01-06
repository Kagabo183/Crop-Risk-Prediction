#!/usr/bin/env python3
"""
Simple markdown to PDF converter
"""
from fpdf import FPDF
from pathlib import Path
import re

class SimplePDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(44, 95, 45)
            self.cell(0, 10, txt='Crop Risk Prediction Platform', new_x="LMARGIN", new_y="NEXT", align='C')
            self.cell(0, 10, txt='Complete Documentation', new_x="LMARGIN", new_y="NEXT", align='C')
            self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, txt=f'Page {self.page_no()}', align='C')

def clean_text(text):
    """Remove markdown formatting"""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
    # Remove special characters that cause issues
    text = text.replace('•', '-')
    text = text.replace('→', '->')
    text = text.replace('—', '-')
    text = text.replace(''', "'")
    text = text.replace(''', "'")
    text = text.replace('"', '"')
    text = text.replace('"', '"')
    text = text.replace('…', '...')
    return text

def convert_to_pdf(md_file, pdf_file):
    """Convert markdown to PDF"""
    md_path = Path(md_file)
    if not md_path.exists():
        print(f"Error: {md_file} not found")
        return False
    
    content = md_path.read_text(encoding='utf-8')
    
    pdf = SimplePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    lines = content.split('\n')
    in_code_block = False
    
    for line in lines:
        # Handle code blocks
        if line.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            pdf.set_font('Courier', '', 8)
            pdf.set_text_color(51, 51, 51)
            try:
                clean_line = clean_text(line)
                if clean_line:
                    pdf.cell(0, 4, txt=clean_line, new_x="LMARGIN", new_y="NEXT")
            except:
                pass
            continue
        
        # Skip empty lines
        if not line.strip():
            pdf.ln(2)
            continue
        
        # Clean the text
        line = clean_text(line)
        
        # Headers
        if line.startswith('# '):
            pdf.set_font('Helvetica', 'B', 16)
            pdf.set_text_color(44, 95, 45)
            pdf.ln(5)
            pdf.multi_cell(0, 8, txt=line[2:])
            pdf.ln(2)
        elif line.startswith('## '):
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(58, 122, 60)
            pdf.ln(3)
            pdf.multi_cell(0, 7, txt=line[3:])
            pdf.ln(2)
        elif line.startswith('### '):
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(74, 138, 76)
            pdf.ln(2)
            pdf.multi_cell(0, 6, txt=line[4:])
            pdf.ln(1)
        elif line.startswith('#### '):
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(90, 154, 92)
            pdf.multi_cell(0, 6, txt=line[5:])
            pdf.ln(1)
        # List items
        elif line.startswith('- ') or line.startswith('* '):
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(51, 51, 51)
            pdf.cell(5, 5, txt='')
            pdf.multi_cell(0, 5, txt=line)
        # Regular text
        else:
            if line.strip():
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(51, 51, 51)
                pdf.multi_cell(0, 5, txt=line)
    
    # Save PDF
    try:
        pdf.output(pdf_file)
        file_size = Path(pdf_file).stat().st_size
        print(f"\n✓ PDF successfully created!")
        print(f"  File: {pdf_file}")
        print(f"  Size: {file_size / 1024:.1f} KB")
        print(f"  Pages: {pdf.page_no()}")
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False

if __name__ == "__main__":
    md_file = "COMPLETE_PROJECT_DOCUMENTATION.md"
    pdf_file = "COMPLETE_PROJECT_DOCUMENTATION.pdf"
    
    print("Converting documentation to PDF...")
    print("This may take a minute...\n")
    convert_to_pdf(md_file, pdf_file)
