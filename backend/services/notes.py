from fpdf import FPDF
from services.rag import query_video, get_concepts

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Important Topics & Notes', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_important_notes_pdf():
    """Generate a PDF of important notes using extracted concepts and a single RAG call."""
    concepts = get_concepts()
    
    pdf = PDF()
    pdf.add_page()
    
    if not concepts:
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "No concepts were extracted. Please load a video first.")
        return pdf.output(dest='S').encode('latin-1')
    
    # Build a single query with all concepts
    concepts_list = ", ".join(concepts)
    query = f"Explain the following concepts in detail, one paragraph per concept with timestamps: {concepts_list}"
    
    try:
        result = query_video(query)
        content = result.get('answer', 'Explanation not available.')
    except Exception as e:
        content = f"Error generating notes: {str(e)}"
    
    pdf.set_font("Arial", size=12)
    safe_content = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, safe_content)
    
    return pdf.output(dest='S').encode('latin-1')

