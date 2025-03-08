import os
import sys
import subprocess
import tempfile
import markdown

def markdown_to_html(markdown_file, html_file):
    """Convert Markdown to HTML"""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Convert markdown to HTML
    html = markdown.markdown(
        markdown_text,
        extensions=['extra', 'codehilite', 'tables', 'toc']
    )
    
    # Create a complete HTML document with styling
    complete_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>OpenManus 代码分析</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                margin: 2cm;
                font-size: 12pt;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #333;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            h1 {{
                font-size: 2em;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.3em;
            }}
            h2 {{
                font-size: 1.5em;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.3em;
            }}
            code {{
                background-color: #f6f8fa;
                border-radius: 3px;
                font-family: monospace;
                padding: 0.2em 0.4em;
            }}
            pre {{
                background-color: #f6f8fa;
                border-radius: 3px;
                padding: 16px;
                overflow: auto;
            }}
            blockquote {{
                border-left: 4px solid #ddd;
                padding-left: 1em;
                color: #777;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            table, th, td {{
                border: 1px solid #ddd;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            ul, ol {{
                padding-left: 2em;
            }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    '''
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(complete_html)
    
    return html_file

def html_to_pdf_with_chrome(html_file, pdf_file):
    """Convert HTML to PDF using Chrome/Chromium"""
    try:
        # Try to find Chrome or Chromium
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
            '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
            '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
            '/Applications/Safari.app/Contents/MacOS/Safari'
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if not chrome_path:
            raise Exception("No compatible browser found")
        
        # Convert HTML to PDF using Chrome headless mode
        cmd = [
            chrome_path,
            '--headless',
            '--disable-gpu',
            f'--print-to-pdf={pdf_file}',
            f'file://{os.path.abspath(html_file)}'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Error converting with Chrome: {e}")
        return False

def html_to_pdf_with_wkhtmltopdf(html_file, pdf_file):
    """Convert HTML to PDF using wkhtmltopdf if available"""
    try:
        subprocess.run(['wkhtmltopdf', html_file, pdf_file], check=True, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("wkhtmltopdf not available or failed")
        return False

def html_to_pdf_with_cupsfilter(html_file, pdf_file):
    """Convert HTML to PDF using macOS cupsfilter"""
    try:
        subprocess.run(['cupsfilter', html_file], stdout=open(pdf_file, 'wb'), check=True)
        return True
    except subprocess.SubprocessError as e:
        print(f"Error converting with cupsfilter: {e}")
        return False

def convert_markdown_to_pdf(markdown_file, pdf_file):
    """Convert Markdown to PDF using available methods"""
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
        temp_html = temp.name
    
    # Convert Markdown to HTML
    html_file = markdown_to_html(markdown_file, temp_html)
    
    # Try different methods to convert HTML to PDF
    success = False
    
    # Method 1: Try Chrome/Chromium
    if not success:
        success = html_to_pdf_with_chrome(html_file, pdf_file)
    
    # Method 2: Try wkhtmltopdf
    if not success:
        success = html_to_pdf_with_wkhtmltopdf(html_file, pdf_file)
    
    # Method 3: Try cupsfilter (macOS)
    if not success:
        success = html_to_pdf_with_cupsfilter(html_file, pdf_file)
    
    # Clean up temporary file
    try:
        os.unlink(temp_html)
    except:
        pass
    
    if success:
        print(f"Successfully converted {markdown_file} to {pdf_file}")
        return True
    else:
        print(f"Failed to convert {markdown_file} to {pdf_file}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_md_to_pdf.py input.md output.pdf")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    pdf_file = sys.argv[2]
    
    if not os.path.exists(markdown_file):
        print(f"Error: File {markdown_file} not found")
        sys.exit(1)
    
    convert_markdown_to_pdf(markdown_file, pdf_file)
