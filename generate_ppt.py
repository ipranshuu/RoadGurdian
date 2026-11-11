from pptx import Presentation

def create_hackathon_ppt():
    prs = Presentation()

    # Slide 1: Title
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "RoadGuardian"
    subtitle.text = "AI-Powered Pothole Detection & Automated Municipal Reporting\n\nPranshu Tiwari\nShivalik College of Engineering\nSmart India Hackathon 2026"

    # Slide 2: The Problem Landscape
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "The Problem Landscape"
    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Public Safety Hazard: Undocumented potholes lead to severe traffic accidents and delays."
    tf.add_paragraph().text = "Friction in Reporting: Relies on manual citizen reporting with low participation."
    tf.add_paragraph().text = "Municipal Blind Spots: Authorities lack a centralized, real-time tracking dashboard."

    # Slide 3: The Solution
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "The RoadGuardian Solution"
    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Automated Data Capture: Ingests geographical coordinates and AI confidence scores."
    tf.add_paragraph().text = "Verified Workflow: Strict state-machine progression prevents spam."
    tf.add_paragraph().text = "Idempotent Submission: Robust backend ensures no duplicate government complaints."

    # Slide 4: Core Technical Architecture
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Core Technical Architecture"
    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Backend Framework: FastAPI for high-performance, async REST routing."
    tf.add_paragraph().text = "Database & ORM: SQLite & SQLAlchemy for persistent data storage."
    tf.add_paragraph().text = "Frontend Foundation: React & Vite for component-based UI."
    tf.add_paragraph().text = "Mapping & Analytics: React-Leaflet & Recharts for geographic plotting."
    tf.add_paragraph().text = "Testing: Pytest & Uvicorn ensuring zero-conflict deployments."

    # Slide 5: System Workflow
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "System Workflow & API Lifecycle"
    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "1. Ingestion: POST /observations"
    tf.add_paragraph().text = "2. Validation: POST /issues/{id}/confirm"
    tf.add_paragraph().text = "3. Generation: POST /issues/{id}/complaint-draft"
    tf.add_paragraph().text = "4. Authorization: POST /complaints/{id}/approve"
    tf.add_paragraph().text = "5. Dispatch: POST /complaints/{id}/submit"

    # Slide 6: Dashboard Interface
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Dashboard Interface"
    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Real-Time Heatmaps: Utilizing Leaflet to cluster pothole observations."
    tf.add_paragraph().text = "Status Tracking: Visual queues to monitor drafts vs. submitted complaints."
    tf.add_paragraph().text = "Analytics Panel: Recharts-driven graphs displaying detection frequency."

    # Slide 7: Impact & Future Scope
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Impact, Scalability & Future Scope"
    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Cost-Effective Governance: Reduces manual overhead for surveying roads."
    tf.add_paragraph().text = "Production-Ready Scalability: One-line migration to PostgreSQL."
    tf.add_paragraph().text = "Future Integrations: Direct municipal API links and predictive AI modeling."

    # Save the file
    filename = "RoadGuardian_SIH2026.pptx"
    prs.save(filename)
    print(f"Success! Presentation saved as {filename}")

if __name__ == "__main__":
    create_hackathon_ppt()