import streamlit as st
import tempfile
import os
import json
import time
import sys
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Fix path resolution for local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import database as db
import curriculum

db.init_db()

st.set_page_config(page_title="Teacher Question Bank", layout="wide")
st.title("📚 Teacher's Question Bank")

api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if not api_key:
    st.info("👈 Please enter your Gemini API Key in the sidebar to proceed.")
    st.stop()

# Force standard v1 API endpoint
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(api_version="v1")
)

class ExtractedQuestion(BaseModel):
    question_text: str = Field(description="Full text of the question, including options if multiple choice.")
    subject: str = Field(description="Subject name: English, Dzongkha, Mathematics, Science, Biology, Physics, Chemistry, History, Geography, Economics, or ICT.")
    grade_level: str = Field(description="Grade level from Grade 7 to Grade 12.")
    topic: str = Field(description="Main academic topic covered by this question.")
    subtopic: str = Field(description="Specific subtopic if applicable, or N/A.")
    marks: int = Field(description="Mark/score assigned to the question if stated, otherwise 1.")

class QuestionList(BaseModel):
    questions: list[ExtractedQuestion]

# Top level navigation
tab_upload, tab_bank = st.tabs(["📤 Upload Exam Paper", "📖 Question Bank"])

# ==========================================
# 1. UPLOAD SECTION
# ==========================================
with tab_upload:
    st.header("Upload Document")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        school_name = st.text_input("School Name", value="Central School")
    with col2:
        exam_year = st.selectbox("Exam Year", [str(y) for y in range(2026, 2014, -1)])
    with col3:
        assessment_type = st.selectbox(
            "Assessment Type",
            ["Unit Test", "Mid-Term Exam", "Trial Exam", "Annual Exam", "Board Exam"]
        )
    with col4:
        default_subject = st.selectbox(
            "Primary Subject Hint",
            ["Auto-detect", "English", "Dzongkha", "Mathematics", "Science", "Biology", "Physics", "Chemistry", "History", "Geography", "Economics", "ICT"]
        )

    uploaded_file = st.file_uploader("Upload Question Paper (PDF, Word, or Image)", type=["pdf", "docx", "png", "jpg", "jpeg"])

    if uploaded_file and st.button("Process & Save Questions"):
        with st.spinner("Analyzing document with Gemini AI..."):
            tmp_file_path = None
            try:
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                gemini_file = client.files.upload(file=tmp_file_path)

                curriculum_guide = json.dumps(curriculum.CURRICULUM, indent=2)

                prompt = f"""
                You are an expert curriculum assistant. Analyze this test document and extract every individual question.

                For each question:
                1. Identify the Subject and Grade Level (Grade 7 to Grade 12).
                2. Categorize the Topic/Subtopic strictly using the predefined curriculum guide below for that subject and grade level.

                Predefined Curriculum Reference:
                {curriculum_guide}

                If a question matches a subtopic listed in the reference above for that subject and grade, output that exact subtopic name as the topic. 
                If it does not match or the subject isn't listed, provide the most concise and accurate topic name.

                Document hint subject: {default_subject}
                """

                models_to_try = ['gemini-3.8-flash', 'gemini-3.5-flash']
                response = None
                last_error = None

                for model_name in models_to_try:
                    for attempt in range(3):
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=[gemini_file, prompt],
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json",
                                    response_schema=QuestionList,
                                )
                            )
                            if response and response.text:
                                break
                        except Exception as e:
                            last_error = e
                            if "503" in str(e) or "UNAVAILABLE" in str(e):
                                time.sleep(2)
                            else:
                                break
                    if response and response.text:
                        break

                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)

                if response and response.text:
                    parsed_data = json.loads(response.text)
                    extracted_questions = parsed_data.get("questions", [])

                    if extracted_questions:
                        for q in extracted_questions:
                            db.insert_question(
                                question_text=q["question_text"],
                                subject=q["subject"],
                                grade_level=q["grade_level"],
                                topic=q["topic"],
                                subtopic=q.get("subtopic", ""),
                                school_name=school_name,
                                year=exam_year,
                                assessment_type=assessment_type,
                                marks=q["marks"]
                            )
                        st.success(f"Successfully saved {len(extracted_questions)} questions under '{assessment_type}' ({school_name}, {exam_year})!")
                    else:
                        st.warning("No questions could be extracted. Please check document clarity.")
                else:
                    st.error(f"Error processing file: {str(last_error)}")

            except Exception as main_e:
                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                st.error(f"Error processing file: {str(main_e)}")

# ==========================================
# 2. QUESTION BANK SECTION (5 ASSESSMENT TABS)
# ==========================================
with tab_bank:
    st.header("Question Bank Archive")

    # Global Filters
    col_s, col_g, col_t = st.columns(3)
    with col_s:
        filter_subject = st.selectbox("Filter by Subject", ["All", "English", "Dzongkha", "Mathematics", "Science", "Biology", "Physics", "Chemistry", "History", "Geography", "Economics", "ICT"])
    with col_g:
        filter_grade = st.selectbox("Filter by Grade", ["All", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"])
    with col_t:
        filter_topic = st.text_input("Search Topic Keyphrase", value="")

    st.markdown("---")

    # 5 Main Assessment Tabs
    tab_ut, tab_mid, tab_trial, tab_annual, tab_board = st.tabs([
        "📝 Unit Tests", 
        "📑 Mid-Term Exams", 
        "🎓 Trial Exams", 
        "🏆 Annual Exams", 
        "🏛️ Board Exams"
    ])

    assessment_categories = [
        (tab_ut, "Unit Test"),
        (tab_mid, "Mid-Term Exam"),
        (tab_trial, "Trial Exam"),
        (tab_annual, "Annual Exam"),
        (tab_board, "Board Exam")
    ]

    for current_tab, category_name in assessment_categories:
        with current_tab:
            questions = db.get_questions_by_assessment(
                assessment_type=category_name,
                subject=filter_subject,
                grade=filter_grade,
                topic=filter_topic
            )

            st.subheader(f"{category_name} Questions ({len(questions)} Found)")

            if not questions:
                st.info(f"No questions saved under {category_name} yet matching your filters.")
            else:
                for q in questions:
                    q_id, q_text, q_subj, q_grade, q_topic, q_subtopic, q_school, q_year, q_marks = q
                    with st.expander(f"[{q_subj} | {q_grade}] Topic: {q_topic} ({q_school} - {q_year} | {q_marks} Marks)"):
                        st.write(f"**Question:** {q_text}")
                        if q_subtopic and q_subtopic != "N/A":
                            st.caption(f"Subtopic: {q_subtopic}")
                        st.caption(f"Source: {q_school} ({q_year})")