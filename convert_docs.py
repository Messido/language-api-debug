import os
import docx
from pathlib import Path

def convert_docx_to_md(docx_path):
    try:
        doc = docx.Document(docx_path)
        md_lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # Simple heuristic for headers based on style name
            style_name = para.style.name.lower()
            if 'heading 1' in style_name:
                md_lines.append(f'# {text}')
            elif 'heading 2' in style_name:
                md_lines.append(f'## {text}')
            elif 'heading 3' in style_name:
                md_lines.append(f'### {text}')
            elif 'list' in style_name or para.style.name.startswith('List'):
                md_lines.append(f'- {text}')
            else:
                md_lines.append(text)
            
            md_lines.append('') # Add newline after each paragraph

        md_content = '\n'.join(md_lines)
        
        md_path = docx_path.with_suffix('.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"Converted: {docx_path.name} -> {md_path.name}")
        return True
    except Exception as e:
        print(f"Failed to convert {docx_path.name}: {e}")
        return False

def main():
    # Target directory relative to this script or absolute
    target_dir = Path(r'c:\Users\siddh\Documents\internship-project\current-project\project_resources')
    
    if not target_dir.exists():
        print(f"Directory not found: {target_dir}")
        return

    count = 0
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.docx'):
                file_path = Path(root) / file
                if convert_docx_to_md(file_path):
                    count += 1
    
    print(f"Total files converted: {count}")

if __name__ == "__main__":
    main()
