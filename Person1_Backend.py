import re
import json
from datetime import datetime

import streamlit as st
import pymupdf
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Recruitment Scam Investigation",
    page_icon="🔎",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main {
    padding-top: 20px;
}

.title {
    font-size: 38px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    margin-bottom: 30px;
}

.result-box {
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #dddddd;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="title">🔎 Recruitment Scam Investigation Platform</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Enter or upload suspicious recruitment content to extract important entities.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove too many blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


# ============================================================
# PHONE NUMBER EXTRACTION
# ============================================================

def extract_phone_numbers(text):

    pattern = r"(?:\+91[\s-]?)?[6-9]\d{9}"

    numbers = re.findall(pattern, text)

    normalized = []

    for number in numbers:

        number = re.sub(r"[^\d+]", "", number)

        if number.startswith("+91"):
            normalized_number = number

        elif len(number) == 10:
            normalized_number = "+91" + number

        else:
            continue

        if normalized_number not in normalized:
            normalized.append(normalized_number)

    return normalized


# ============================================================
# EMAIL EXTRACTION
# ============================================================

def extract_emails(text):

    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    emails = re.findall(pattern, text)

    emails = list(dict.fromkeys(emails))

    return emails


# ============================================================
# URL EXTRACTION
# ============================================================

def extract_urls(text):

    pattern = r"(?:https?://|www\.)[^\s]+"

    urls = re.findall(pattern, text)

    cleaned_urls = []

    for url in urls:

        url = url.rstrip(".,;:!?)]}")

        if url not in cleaned_urls:
            cleaned_urls.append(url)

    return cleaned_urls


# ============================================================
# USERNAME EXTRACTION
# ============================================================

def extract_usernames(text):

    pattern = r"(?<!\w)@[A-Za-z0-9_]{3,30}"

    usernames = re.findall(pattern, text)

    usernames = list(dict.fromkeys(usernames))

    return usernames


# ============================================================
# UPI ID EXTRACTION
# ============================================================

def extract_upi_ids(text):

    pattern = r"\b[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\b"

    possible_upi = re.findall(pattern, text)

    upi_ids = []

    for item in possible_upi:

        # Email-like values containing a domain dot
        # are not treated as UPI IDs
        if "." in item.split("@")[-1]:
            continue

        if item not in upi_ids:
            upi_ids.append(item)

    return upi_ids


# ============================================================
# ORGANIZATION EXTRACTION
# ============================================================

def extract_organizations(text):

    organizations = []

    patterns = [

        r"\b[A-Z][A-Za-z& ]{2,50}\s+(?:Ltd|Limited|Pvt Ltd|Private Limited|LLP|Inc|Corporation|Corp)\b",

        r"\b(?:Google|Microsoft|Amazon|Infosys|TCS|Wipro|Accenture|Deloitte)\b"

    ]

    for pattern in patterns:

        matches = re.findall(pattern, text)

        for match in matches:

            match = match.strip()

            if match not in organizations:
                organizations.append(match)

    return organizations


# ============================================================
# ENTITY EXTRACTION
# ============================================================

def extract_entities(text):

    entities = {

        "phone_numbers": extract_phone_numbers(text),

        "emails": extract_emails(text),

        "urls": extract_urls(text),

        "usernames": extract_usernames(text),

        "upi_ids": extract_upi_ids(text),

        "organizations": extract_organizations(text)

    }

    return entities


# ============================================================
# IMAGE OCR
# ============================================================

def extract_text_from_image(image_file):

    try:

        image = Image.open(image_file)

        extracted_text = pytesseract.image_to_string(image)

        return extracted_text.strip()

    except Exception as e:

        st.error("Image OCR failed.")
        st.error(str(e))

        return ""


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(pdf_file):

    try:

        pdf_bytes = pdf_file.read()

        document = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        pages_text = []

        for page in document:

            page_text = page.get_text()

            if page_text:
                pages_text.append(page_text)

        document.close()

        return "\n".join(pages_text).strip()

    except Exception as e:

        st.error("PDF processing failed.")
        st.error(str(e))

        return ""


# ============================================================
# TXT FILE EXTRACTION
# ============================================================

def extract_text_from_txt(txt_file):

    try:

        file_bytes = txt_file.read()

        text = file_bytes.decode("utf-8", errors="ignore")

        return text.strip()

    except Exception as e:

        st.error("TXT file processing failed.")
        st.error(str(e))

        return ""


# ============================================================
# CREATE STRUCTURED CASE
# ============================================================

def create_case(text, entities, input_type):

    case_id = "CASE-" + datetime.now().strftime("%Y%m%d%H%M%S")

    case = {

        "case_id": case_id,

        "created_at": datetime.now().isoformat(),

        "input_type": input_type,

        "raw_text": text,

        "entities": entities,

        "status": "Pending Investigation"

    }

    return case


# ============================================================
# USER INPUT SECTION
# ============================================================

st.header("1️⃣ Enter Suspicious Recruitment Information")

st.write(
    "Paste the suspicious job/recruitment message below "
    "OR upload a file."
)


user_text = st.text_area(
    "Paste suspicious recruitment message:",
    height=220,
    placeholder=(
        "Example: You have been selected for a work-from-home job. "
        "Contact us on WhatsApp..."
    )
)


st.markdown("### OR")


uploaded_file = st.file_uploader(
    "Upload recruitment evidence",
    type=[
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "webp",
        "txt"
    ]
)


# ============================================================
# ANALYZE BUTTON
# ============================================================

analyze_button = st.button(
    "🔍 Analyze Recruitment Data",
    type="primary",
    use_container_width=True
)


# ============================================================
# PROCESS USER INPUT
# ============================================================

if analyze_button:

    extracted_text = ""
    input_type = ""

    # --------------------------------------------------------
    # PRIORITY 1: TEXT ENTERED BY USER
    # --------------------------------------------------------

    if user_text.strip():

        extracted_text = clean_text(user_text)

        input_type = "User Entered Text"

    # --------------------------------------------------------
    # PRIORITY 2: UPLOADED FILE
    # --------------------------------------------------------

    elif uploaded_file is not None:

        file_name = uploaded_file.name.lower()

        # PDF
        if file_name.endswith(".pdf"):

            input_type = "PDF"

            extracted_text = extract_text_from_pdf(
                uploaded_file
            )

        # IMAGE
        elif file_name.endswith(
            (".png", ".jpg", ".jpeg", ".webp")
        ):

            input_type = "Image"

            st.image(
                uploaded_file,
                caption="Uploaded Recruitment Evidence",
                use_container_width=True
            )

            extracted_text = extract_text_from_image(
                uploaded_file
            )

        # TXT
        elif file_name.endswith(".txt"):

            input_type = "TXT"

            extracted_text = extract_text_from_txt(
                uploaded_file
            )

        extracted_text = clean_text(extracted_text)

    # --------------------------------------------------------
    # NOTHING PROVIDED
    # --------------------------------------------------------

    else:

        st.warning(
            "Please enter recruitment text or upload a file."
        )

        st.stop()

    # --------------------------------------------------------
    # CHECK EXTRACTED TEXT
    # --------------------------------------------------------

    if not extracted_text:

        st.error(
            "No readable text was found in the provided input."
        )

        st.stop()

    # --------------------------------------------------------
    # ENTITY EXTRACTION
    # --------------------------------------------------------

    entities = extract_entities(
        extracted_text
    )

    # --------------------------------------------------------
    # CREATE CASE
    # --------------------------------------------------------

    case = create_case(
        extracted_text,
        entities,
        input_type
    )

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    st.success(
        "Analysis completed successfully!"
    )

    # --------------------------------------------------------
    # EXTRACTED TEXT
    # --------------------------------------------------------

    st.header("2️⃣ Extracted Recruitment Content")

    st.text_area(
        "Processed Text",
        extracted_text,
        height=250
    )

    # --------------------------------------------------------
    # ENTITIES
    # --------------------------------------------------------

    st.header("3️⃣ Extracted Entities")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📱 Phone Numbers")

        if entities["phone_numbers"]:

            for phone in entities["phone_numbers"]:
                st.write("•", phone)

        else:

            st.write("No phone numbers found.")

        st.subheader("📧 Email Addresses")

        if entities["emails"]:

            for email in entities["emails"]:
                st.write("•", email)

        else:

            st.write("No email addresses found.")

        st.subheader("🌐 URLs")

        if entities["urls"]:

            for url in entities["urls"]:
                st.write("•", url)

        else:

            st.write("No URLs found.")

    with col2:

        st.subheader("👤 Usernames")

        if entities["usernames"]:

            for username in entities["usernames"]:
                st.write("•", username)

        else:

            st.write("No usernames found.")

        st.subheader("💳 UPI IDs")

        if entities["upi_ids"]:

            for upi in entities["upi_ids"]:
                st.write("•", upi)

        else:

            st.write("No UPI IDs found.")

        st.subheader("🏢 Organizations")

        if entities["organizations"]:

            for organization in entities["organizations"]:
                st.write("•", organization)

        else:

            st.write("No organizations found.")

    # --------------------------------------------------------
    # STRUCTURED CASE
    # --------------------------------------------------------

    st.header("4️⃣ Structured Case")

    st.json(case)

    # --------------------------------------------------------
    # DOWNLOAD JSON
    # --------------------------------------------------------

    json_data = json.dumps(
        case,
        indent=4,
        ensure_ascii=False
    )

    st.download_button(
        label="⬇️ Download Case JSON",
        data=json_data,
        file_name=f"{case['case_id']}.json",
        mime="application/json",
        use_container_width=True
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    st.header("5️⃣ Investigation Status")

    st.info(
        "Status: Pending Investigation\n\n"
        "The system has extracted and structured the available "
        "information. It does not independently declare a person "
        "or organization as a scammer."
    )