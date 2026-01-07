import os
import re
from pathlib import Path

# Configuration
SOURCE_DIR = Path(r"c:\Users\siddh\Documents\internship-project\current-project\project_resources\markdown_exports")
OUTPUT_FILE = SOURCE_DIR / "analytics_mentions.md"

# Keywords to search for (case-insensitive)
KEYWORDS = [
    "analytics", "track", "monitor", "stat", "report", "progress", 
    "perform", "score", "result", "dashboard", "checklist", "completion",
    "strength", "weakness", "timeline", "log", "assess", "evaluate"
]

def get_paragraphs(content):
    # Split by double newlines to roughly approximate paragraphs
    # Return list of (start_line, content) tuples
    lines = content.split('\n')
    paragraphs = []
    current_para = []
    start_line = 1
    current_line = 1
    
    for line in lines:
        if line.strip() == '':
            if current_para:
                paragraphs.append({
                    'start': start_line,
                    'end': current_line - 1,
                    'text': '\n'.join(current_para)
                })
                current_para = []
            start_line = current_line + 1
        else:
            if not current_para:
                start_line = current_line
            current_para.append(line)
        current_line += 1
        
    if current_para:
        paragraphs.append({
            'start': start_line,
            'end': current_line - 1,
            'text': '\n'.join(current_para)
        })
        
    return paragraphs

def find_analytics_context_detailed():
    if not SOURCE_DIR.exists():
        print(f"Directory not found: {SOURCE_DIR}")
        return

    output_lines = ["# Analytics and Tracking References (Comprehensive)\n"]
    output_lines.append("This document contains extended context (preceding and following paragraphs) for all analytics and tracking references.\n")

    files_to_scan = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".md") and f != "analytics_mentions.md"]

    for filename in files_to_scan:
        file_path = SOURCE_DIR / filename
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            paragraphs = get_paragraphs(content)
            interesting_indices = set()
            
            # 1. Identify interesting paragraphs
            for i, para in enumerate(paragraphs):
                lower_text = para['text'].lower()
                if any(k in lower_text for k in KEYWORDS):
                    interesting_indices.add(i)
            
            if not interesting_indices:
                continue

            # 2. Expand context (add +/- 1 paragraph)
            expanded_indices = set()
            for i in interesting_indices:
                expanded_indices.add(max(0, i - 1)) # Preceding
                expanded_indices.add(i)             # Current
                expanded_indices.add(min(len(paragraphs) - 1, i + 1)) # Following
            
            # 3. Create merged distinct ranges
            sorted_indices = sorted(list(expanded_indices))
            ranges = []
            if sorted_indices:
                start_i = sorted_indices[0]
                prev_i = sorted_indices[0]
                
                for i in sorted_indices[1:]:
                    if i > prev_i + 1:
                        # Gap found, close current range
                        ranges.append((start_i, prev_i))
                        start_i = i
                    prev_i = i
                ranges.append((start_i, prev_i))

            # 4. Generate Output
            output_lines.append(f"## {filename}\n")
            
            for start_idx, end_idx in ranges:
                # Get line number range for the whole block
                block_start_line = paragraphs[start_idx]['start']
                block_end_line = paragraphs[end_idx]['end']
                
                output_lines.append(f"### Lines {block_start_line} - {block_end_line}")
                
                # formatting the block
                block_content = []
                for i in range(start_idx, end_idx + 1):
                    # Highlight keywords in the matching paragraph specifically? 
                    # For now just dump the text. To differentiate, we could bold the matching para?
                    # Let's just output the text as blockquotes.
                    
                    para_text = paragraphs[i]['text']
                    # Check if this specific paragraph has a match to maybe mark it?
                    # (Optional, keeping it simple for now)
                    
                    quoted_para = "\n".join([f"> {line}" for line in para_text.split('\n')])
                    block_content.append(quoted_para)
                
                output_lines.append("\n>\n".join(block_content)) # Separate paragraphs with a spacer quote line
                output_lines.append("\n\n---\n")

        except Exception as e:
            print(f"Error reading {filename}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(output_lines)
    
    print(f"Generated comprehensive report at: {OUTPUT_FILE}")

if __name__ == "__main__":
    find_analytics_context_detailed()
