import markdown
import os
import sys
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def markdown_to_pdf(markdown_file, pdf_file):
    """
    Convert a Markdown file to PDF using WeasyPrint
    """
    # Read the markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Convert markdown to HTML
    html = markdown.markdown(
        markdown_text,
        extensions=['extra', 'codehilite', 'tables', 'toc']
    )
    
    # Add some basic styling
    css = CSS(string='''
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            margin: 2cm;
            font-size: 12pt;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #333;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        h1 {
            font-size: 2em;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.3em;
        }
        h2 {
            font-size: 1.5em;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.3em;
        }
        code {
            background-color: #f6f8fa;
            border-radius: 3px;
            font-family: monospace;
            padding: 0.2em 0.4em;
        }
        pre {
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }
        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 1em;
            color: #777;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        ul, ol {
            padding-left: 2em;
        }
    ''')
    
    # Create a complete HTML document
    complete_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>OpenManus 代码分析</title>
    </head>
    <body>
        {html}
    </body>
    </html>
    '''
    
    # Generate PDF
    font_config = FontConfiguration()
    HTML(string=complete_html).write_pdf(
        pdf_file,
        stylesheets=[css],
        font_config=font_config
    )
    
    print(f"Successfully converted {markdown_file} to {pdf_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_to_pdf.py input.md output.pdf")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    pdf_file = sys.argv[2]
    
    if not os.path.exists(markdown_file):
        print(f"Error: File {markdown_file} not found")
        sys.exit(1)
    
    markdown_to_pdf(markdown_file, pdf_file)
