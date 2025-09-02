# create_test_pdfs.py
from fpdf import FPDF
import os

def create_simple_pdf(text, output_path):
    class PDF(FPDF):
        def header(self):
            pass
        def footer(self):
            pass

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Add some padding at the top
    pdf.ln(10)
    
    # Split text into lines and add to PDF
    lines = text.split('\n')
    for line in lines:
        # Replace bullet points with simple dashes
        line = line.replace('•', '-')
        # Encode safely
        safe_line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, txt=safe_line, ln=True)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the PDF
    pdf.output(output_path)

def create_test_data():
    # Create base directories
    for candidate_id in [2, 3, 4, 5, 6]:
        os.makedirs(f"test_data/{candidate_id}", exist_ok=True)

    # Sample resume text
    resume_text = """JOHN DOE
Software Engineer

EDUCATION
Bachelor of Science in Computer Science
University of Technology (2018-2022)

EXPERIENCE
Software Developer Intern
Tech Company Inc. (Summer 2021)
- Developed web applications using Python
- Collaborated with team of 5 developers
- Implemented new features for main product

PROJECTS
Personal Website
- Built responsive website using React
- Implemented backend using Node.js
- Deployed on AWS

SKILLS
- Programming: Python, JavaScript, Java
- Web: React, Node.js, HTML/CSS
- Tools: Git, Docker, AWS"""

    # Sample supplemental text
    supplemental_text = """ADDITIONAL INFORMATION

CERTIFICATIONS
- AWS Certified Developer
- Google Cloud Professional

VOLUNTEER WORK
Code Teacher
Local High School
- Taught basic programming to students
- Organized coding workshops

PUBLICATIONS
- "Modern Web Development" - Tech Blog
- "Python Best Practices" - Medium"""

    # Create PDFs for each candidate
    for candidate_id in [2, 3, 4, 5, 6]:
        print(f"Creating PDFs for candidate {candidate_id}...")
        
        # Create main resume
        main_pdf_path = f"test_data/{candidate_id}/file_0.pdf"
        create_simple_pdf(resume_text, main_pdf_path)
        print(f"Created main resume: {main_pdf_path}")
        
        # Create supplemental info for some candidates
        if candidate_id in [2, 4, 6]:
            supp_pdf_path = f"test_data/{candidate_id}/supplemental.pdf"
            create_simple_pdf(supplemental_text, supp_pdf_path)
            print(f"Created supplemental info: {supp_pdf_path}")

if __name__ == "__main__":
    print("Starting PDF creation...")
    create_test_data()
    print("PDF creation complete!")