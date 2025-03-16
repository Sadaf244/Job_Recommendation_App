from PyPDF2 import PdfReader
from docx import Document
from django.conf import settings
from openai import OpenAI
import json
import re
from jobs.job_data import SKILL_ONTOLOGY
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def standardize_skills(skills):
    """
    Standardize skills using a predefined ontology.
    """
    standardized_skills = set()
    for skill in skills:
        for key, synonyms in SKILL_ONTOLOGY.items():
            if skill.lower() in synonyms:
                standardized_skills.add(key)
    return list(standardized_skills)
def parse_resume(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Extract the following details from the resume and return the result in JSON format: Name, Email ID, Phone Number, Skills, Overall Total Experience, Qualification."
            },
            {
                "role": "user",
                "content": text
            },
        ],
        max_tokens=500
    )
    parsed_text = response.choices[0].message.content.strip()
    # Extract JSON from the code block (if present)
    json_match = re.search(r"```json\s*({.*?})\s*```", parsed_text, re.DOTALL)
    if json_match:
        json_data = json_match.group(1)
        try:
            # Parse the JSON data
            structured_data = json.loads(json_data)
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to the previous parsing logic
            structured_data = parse_fallback(parsed_text)
    else:
        # If no JSON code block is found, use the fallback parsing logic
        structured_data = parse_fallback(parsed_text)

    return structured_data

def parse_fallback(parsed_text):
    # Fallback parsing logic for non-JSON responses
    structured_data = {
        "Name": None,
        "Qualification": None,
        "Skills": None,
        "Total Experience": None,
        "Email ID": None,
        "Phone Number": None,
    }

    # Split the parsed text into lines
    lines = parsed_text.split("\n")

    # Iterate through each line and extract the relevant information
    for line in lines:
        line = line.strip()
        if line.startswith("**Name:") or line.startswith("**Name**:"):
            structured_data["Name"] = line.split(":")[1].strip()
        elif line.startswith("**Email ID:") or line.startswith("**Email ID**:"):
            structured_data["Email ID"] = line.split(":")[1].strip()
        elif line.startswith("**Phone Number:") or line.startswith("**Phone Number**:"):
            structured_data["Phone Number"] = line.split(":")[1].strip()
        elif line.startswith("**Skills:") or line.startswith("**Skills**:"):
            structured_data["Skills"] = line.split(":")[1].strip()
        elif line.startswith("**Overall Total Experience:") or line.startswith("**Overall Total Experience**:"):
            structured_data["Total Experience"] = line.split(":")[1].strip()
        elif line.startswith("**Qualification:") or line.startswith("**Qualification**:"):
            # Handle both single-line and multi-line Qualification sections
            qualification_section = line.split(":")[1].strip()
            # Check if the next line starts with "-" (multi-line section)
            next_line_index = lines.index(line) + 1
            if next_line_index < len(lines) and lines[next_line_index].strip().startswith("-"):
                # Collect all lines under the Qualification section
                qualification_lines = []
                for qual_line in lines[next_line_index:]:
                    if qual_line.strip().startswith("-"):
                        qualification_lines.append(qual_line.strip())
                    else:
                        break
                structured_data["Qualification"] = ", ".join(qualification_lines)
            else:
                # Single-line Qualification section
                structured_data["Qualification"] = qualification_section

    return structured_data


def extract_text_from_pdf(file):
    if file.name.lower().endswith('.pdf'):
        reader = PdfReader(file)  # Use PdfReader instead of PdfFileReader
        text = ""
        for page in reader.pages:  # Use `pages` instead of `getPage`
            text += page.extract_text()  # Extract text from each page
        return text
    else:
        raise ValueError("Unsupported file format. Only PDF files are supported.")

def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text





