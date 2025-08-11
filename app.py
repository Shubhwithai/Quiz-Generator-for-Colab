import streamlit as st
import uuid
import os
import tempfile
import hashlib
from reportlab.lib.pagesizes import A5, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from datetime import datetime

# --- Certificate Generator (from original app) ---
def generate_certificate(name, score, total, instructor="Instructor"):
    """
    Generates a PDF certificate of completion.
    """
    unique_id = str(uuid.uuid4())
    filename = f"cert_{unique_id}.pdf"
    filepath = os.path.join(tempfile.gettempdir(), filename)

    c = canvas.Canvas(filepath, pagesize=landscape(A5))
    width, height = landscape(A5)

    # Set background and border
    c.setFillColor(HexColor("#fffdf6")) # Creamy background
    c.rect(0, 0, width, height, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#001858")) # Dark blue border
    c.setLineWidth(3)
    margin = 10 * mm
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    # Add text content
    c.setFillColor(HexColor("#001858")) # Dark blue text
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 60, "Certificate of Completion")

    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 100, "This is awarded to")

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 130, name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 160, "For successfully completing the quiz")

    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 185, f"Score: {score} / {total}")

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(margin + 10, margin + 20, f"Instructor: {instructor}")
    date_str = datetime.now().strftime("%d %B %Y")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - margin - 10, margin + 20, f"Issued on: {date_str}")

    c.save()
    return filepath

# --- Main Quiz Code Generator ---
def generate_python_code(title, instructor, quiz_type, questions_text):
    """
    Parses instructor input and generates a self-contained Python script
    for a student-facing Gradio quiz app.
    """
    # Parse questions and hash the answers for security
    parsed_questions = []
    for line in questions_text.strip().split("\n"):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]

        if quiz_type == "Multiple Choice":
            if len(parts) < 3: continue # Skip malformed lines
            q_text = parts[0]
            options = parts[1:-1]
            answer = parts[-1]
            parsed_questions.append({
                "question": q_text,
                "options": options,
                "answer_hash": hashlib.sha256(answer.lower().encode()).hexdigest()
            })
        else: # Text Answer
            if len(parts) < 2: continue # Skip malformed lines
            q_text = parts[0]
            answer = parts[1]
            parsed_questions.append({
                "question": q_text,
                "answer_hash": hashlib.sha256(answer.lower().encode()).hexdigest()
            })

    # Generate the complete Python code string for the student quiz app
    # f-strings with {{ and }} are used to escape braces for the final code.
    python_code = f'''!pip install gradio reportlab
# --- Generated Quiz App ---
# Copy and paste this entire code block into a single Google Colab cell and run it.

import gradio as gr
import uuid, os, tempfile, hashlib
from reportlab.lib.pagesizes import A5, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from datetime import datetime

# Certificate generation function (included for a self-contained script)
def generate_certificate(name, score, total, instructor="{instructor}"):
    unique_id = str(uuid.uuid4())
    filename = f"cert_{{unique_id}}.pdf"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    c = canvas.Canvas(filepath, pagesize=landscape(A5))
    width, height = landscape(A5)
    c.setFillColor(HexColor("#fffdf6"))
    c.rect(0, 0, width, height, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#001858"))
    c.setLineWidth(3)
    margin = 10 * mm
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)
    c.setFillColor(HexColor("#001858"))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 60, "Certificate of Completion")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 100, "This is awarded to")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 130, name)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 160, "For successfully completing the quiz")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 185, f"Score: {{score}} / {{total}}")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(margin + 10, margin + 20, f"Instructor: {{instructor}}")
    date_str = datetime.now().strftime("%d %B %Y")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - margin - 10, margin + 20, f"Issued on: {{date_str}}")
    c.save()
    return filepath

# Quiz data (answers are hashed)
quiz_type = "{quiz_type}"
questions = {parsed_questions}

def eval_quiz(name, *answers):
    """
    Evaluates the student's answers and generates a certificate only if the score is 80% or higher.
    """
    if not name.strip():
        name = "Anonymous"
    score = 0
    for i, ans in enumerate(answers):
        if ans and hashlib.sha256(str(ans).lower().strip().encode()).hexdigest() == questions[i]["answer_hash"]:
            score += 1
    
    total_questions = len(questions)
    passing_threshold = 0.8
    
    result_message = f"Hi {{name}}, your score is: {{score}} / {{total_questions}}."
    cert_path = None # Default to no certificate

    # Check if the score meets the passing threshold
    if total_questions > 0 and (score / total_questions) >= passing_threshold:
        cert_path = generate_certificate(name, score, total_questions, instructor="{instructor}")
        result_message += " Congratulations, you passed and earned a certificate!"
    else:
        result_message += " A score of 80% is required to receive a certificate."

    return result_message, cert_path

# Gradio interface for the student
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("## {title}")
    
    with gr.Row():
        name = gr.Textbox(label="Enter Your Full Name to Generate Certificate", placeholder="e.g., Ada Lovelace")

    answer_inputs = []
    for q in questions:
        gr.Markdown("**Question:** " + q['question'])
        if quiz_type == "Multiple Choice":
            answer_inputs.append(gr.Radio(choices=q["options"], label="Select your answer"))
        else:
            answer_inputs.append(gr.Textbox(label="Type your answer"))

    submit_btn = gr.Button("Submit Quiz")
    
    with gr.Row():
        result_output = gr.Textbox(label="Your Result")
        certificate_output = gr.File(label="Download Your Certificate")

    submit_btn.click(
        fn=eval_quiz, 
        inputs=[name] + answer_inputs, 
        outputs=[result_output, certificate_output]
    )

app.launch(debug=True)
'''
    return python_code

# --- Streamlit UI for Instructor ---
st.set_page_config(page_title="Quiz Generator", layout="center")
st.title("📝 Instructor Quiz Generator for Colab")
st.markdown("Create a secure, interactive quiz, then copy the generated Python code into a Google Colab cell.")

with st.form("quiz_generator_form"):
    st.header("1. Enter Quiz Details")
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Quiz Title", placeholder="e.g. Python Basics Quiz")
        instructor = st.text_input("Instructor Name", placeholder="e.g. Dr. Ada Lovelace")
    with col2:
        quiz_type = st.selectbox("Quiz Type", ["Multiple Choice", "Text Answer"], index=0)
    
    questions_text = st.text_area(
        "Questions & Answers",
        height=250,
        placeholder=(
            "One question per line. Separate parts with commas.\n\n"
            "MCQ Format: Question,Option1,Option2,CorrectOption\n"
            "Text Format: Question,CorrectAnswer"
        )
    )
    
    submitted = st.form_submit_button("🚀 Generate Python Quiz Code")

if submitted:
    if not all([title, instructor, questions_text]):
        st.error("Please fill in all fields to generate the code.")
    else:
        generated_code = generate_python_code(title, instructor, quiz_type, questions_text)
        st.header("2. Copy Your Generated Code")
        st.markdown("Paste this entire code block into a single Google Colab cell and run it.")
        st.code(generated_code, language='python')
