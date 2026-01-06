#!/usr/bin/env python3
"""
Convert markdown documentation to PDF
"""
import markdown2
from pathlib import Path

def markdown_to_html_pdf(md_file, output_file):
    """Convert markdown to PDF via HTML"""
    # Read markdown file
    md_path = Path(md_file)
    if not md_path.exists():
        print(f"Error: {md_file} not found")
        return False
    
    md_content = md_path.read_text(encoding='utf-8')
    
    # Convert to HTML
    html_content = markdown2.markdown(md_content, extras=['tables', 'fenced-code-blocks', 'header-ids'])
    
    # Create styled HTML
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c5f2d;
            border-bottom: 3px solid #2c5f2d;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        h2 {{
            color: #3a7a3c;
            border-bottom: 2px solid #97c498;
            padding-bottom: 8px;
            margin-top: 25px;
        }}
        h3 {{
            color: #4a8a4c;
            margin-top: 20px;
        }}
        h4 {{
            color: #5a9a5c;
            margin-top: 15px;
        }}
        code {{
            background-color: #f4f4f4;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 2px 6px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        pre code {{
            background: none;
            border: none;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background-color: #2c5f2d;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        blockquote {{
            border-left: 4px solid #2c5f2d;
            margin: 15px 0;
            padding-left: 15px;
            color: #666;
        }}
        strong {{
            color: #2c5f2d;
        }}
        a {{
            color: #3a7a3c;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .page-break {{
            page-break-after: always;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
    
    # Save HTML temporarily
    html_path = Path(output_file).with_suffix('.html')
    html_path.write_text(full_html, encoding='utf-8')
    print(f"✓ HTML created: {html_path}")
    
    # Try to convert to PDF using wkhtmltopdf
    try:
        import pdfkit
        pdfkit.from_file(str(html_path), output_file)
        print(f"✓ PDF created: {output_file}")
        return True
    except Exception as e:
        print(f"Note: wkhtmltopdf not found. HTML file created at: {html_path}")
        print(f"You can:")
        print(f"  1. Open {html_path} in a browser and print to PDF")
        print(f"  2. Install wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html")
        print(f"  3. Use an online HTML to PDF converter")
        return False

if __name__ == "__main__":
    md_file = "COMPLETE_PROJECT_DOCUMENTATION.md"
    pdf_file = "COMPLETE_PROJECT_DOCUMENTATION.pdf"
    
    print("Converting documentation to PDF...")
    markdown_to_html_pdf(md_file, pdf_file)
