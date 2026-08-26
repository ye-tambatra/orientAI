import os
import glob
from bs4 import BeautifulSoup
from markdownify import markdownify as md

source_dir = "data/sources"
target_dir = "data/structured"

os.makedirs(target_dir, exist_ok=True)

html_files = glob.glob(os.path.join(source_dir, "*.html"))

for html_file in html_files:
    print(f"Processing {html_file}...")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
        
    markdown_content = md(str(soup), heading_style="ATX", autolinks=False)
    
    # cleanup extra blank lines
    lines = markdown_content.split('\n')
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count > 2:
                continue
        else:
            blank_count = 0
        cleaned_lines.append(line)
        
    markdown_content = '\n'.join(cleaned_lines)
    
    base_name = os.path.basename(html_file)
    name_without_ext = os.path.splitext(base_name)[0]
    target_file = os.path.join(target_dir, f"{name_without_ext}.md")
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"Saved to {target_file}")

