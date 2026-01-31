from fpdf import FPDF
from services.rag import query_video

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Important Topics & Notes', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

async def generate_important_notes_pdf(user_id: str, concepts: list):
    """Generate a PDF of important notes using extracted concepts and a single RAG call."""
    
    pdf = PDF()
    pdf.add_page()
    
    if not concepts:
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "No concepts were extracted. Please load a video first.")
        # pdf.output returns string in older fpdf
        out = pdf.output(dest='S')
        return out.encode('latin-1') if isinstance(out, str) else out
    
    # Build a single query with all concepts
    concepts_list = ", ".join(concepts)
    query = (
        f"Explain the following concepts from the video transcript. "
        f"Format the output such that each concept begins with '### Concept Name' on its own line, "
        f"followed by '**Timestamp:** [HH:MM:SS]' and '**Explanation:** [2-3 sentences]'. "
        f"Ensure there is a blank line between each concept section.\n"
        f"IMPORTANT: Return ONLY the formatted text. DO NOT wrap the output in JSON or code blocks.\n\n"
        f"Concepts: {concepts_list}"
    )
    
    try:
        result = await query_video(query, user_id)
        
        if isinstance(result, dict):
            if 'answer' in result:
                content_val = result['answer']
                if isinstance(content_val, str):
                    content = content_val
                elif isinstance(content_val, (dict, list)):
                    # If answer is a nested structural object, stringify it nicely
                    import json
                    content = json.dumps(content_val, indent=2)
                else:
                    content = str(content_val)
            else:
                # If 'answer' is missing, the LLM might have returned concepts as keys
                # Concatenate all non-timestamp values, stringifying non-strings
                parts = []
                for key, value in result.items():
                    if key != 'timestamp':
                        val_str = value if isinstance(value, str) else str(value)
                        parts.append(f"{key}: {val_str}")
                content = "\n\n".join(parts) if parts else 'Explanation not available.'
        else:
            content = str(result)
            
        # Robustly strip JSON structures if they accidentally leak through
        # e.g. if content itself is '{"answer": "..."}'
        if content.strip().startswith('{') and '"answer":' in content:
            import re
            match = re.search(r'"answer":\s*"(.*?)"', content, re.DOTALL)
            if match:
                content = match.group(1).encode().decode('unicode_escape')
        
        # Strip code block markers
        content = content.replace('```json', '').replace('```', '').strip()
        
    except Exception as e:
        content = f"Error generating notes: {str(e)}"
    
    safe_content = content.encode('latin-1', 'replace').decode('latin-1')
    
    # Simple Markdown-like rendering
    lines = safe_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
            
        if line.startswith('###'):
            # Header
            header_text = line.replace('###', '').strip()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, header_text, 0, 1)
            pdf.set_font("Arial", size=12)
        elif '**' in line:
            # Handle simple bolding e.g. **Timestamp:** 00:01:00
            parts = line.split('**')
            pdf.set_font("Arial", size=12)
            is_bold = False
            for part in parts:
                if not part:
                    is_bold = not is_bold
                    continue
                
                if is_bold:
                    pdf.set_font("Arial", 'B', 12)
                    pdf.write(8, part)
                    pdf.set_font("Arial", '', 12)
                else:
                    pdf.write(8, part)
                is_bold = not is_bold
            pdf.ln(8)
        else:
            # Normal text
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 8, line)
            pdf.ln(2)
    
    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else out

