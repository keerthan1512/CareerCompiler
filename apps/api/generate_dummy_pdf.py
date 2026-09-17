from reportlab.pdfgen import canvas

def generate_pdf(filename="sample_resume.pdf"):
    c = canvas.Canvas(filename)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, "John Doe")
    c.setFont("Helvetica", 12)
    c.drawString(100, 780, "Software Engineer")
    c.drawString(100, 760, "john.doe@example.com | github.com/johndoe")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 720, "Professional Experience")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 700, "Senior Developer at TechCorp")
    c.setFont("Helvetica", 10)
    c.drawString(100, 685, "Jan 2020 - Present | San Francisco, CA")
    
    c.drawString(110, 670, "- Led a team of 5 engineers to build scalable APIs.")
    c.drawString(110, 655, "- Improved database performance by 40%.")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 615, "Education")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 595, "B.S. in Computer Science, University of X")
    c.setFont("Helvetica", 10)
    c.drawString(100, 580, "Sep 2015 - May 2019")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 540, "Skills")
    c.setFont("Helvetica", 12)
    c.drawString(100, 520, "Languages: Python, JavaScript, Go")
    c.drawString(100, 500, "Frameworks: FastAPI, React")
    
    c.save()

if __name__ == "__main__":
    generate_pdf()
    print("Generated sample_resume.pdf")
