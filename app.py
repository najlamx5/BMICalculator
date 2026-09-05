# ============================================================
# BMI CALCULATOR + OCR + AUTO FILL + IDEAL WEIGHT
# GOOGLE COLAB - COMPLETE ONE CELL
# ============================================================

import os
import sys
import subprocess
import time
import re
import urllib.request

# ============================================================
# 1. INSTALL PYTHON PACKAGES
# ============================================================

print("📦 Installing Python packages...")

subprocess.run(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-q",
        "streamlit",
        "pytesseract",
        "Pillow"
    ],
    check=True
)

print("✅ Python packages installed.")


# ============================================================
# 2. INSTALL TESSERACT OCR
# ============================================================

print("📦 Installing Tesseract OCR...")

subprocess.run(
    [
        "bash",
        "-c",
        "apt-get update -qq && apt-get install -y -qq tesseract-ocr"
    ],
    check=True
)

print("✅ Tesseract OCR installed.")


# ============================================================
# 3. INSTALL CLOUDFLARED
# ============================================================

print("📦 Installing Cloudflare Tunnel...")

cloudflared_path = "/usr/local/bin/cloudflared"

if not os.path.exists(cloudflared_path):

    subprocess.run(
        [
            "bash",
            "-c",
            """
            wget -q \
            https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
            -O /tmp/cloudflared.deb

            dpkg -i /tmp/cloudflared.deb
            """
        ],
        check=True
    )

print("✅ Cloudflare Tunnel installed.")


# ============================================================
# 4. CREATE APP.PY
# ============================================================

app_code = r'''
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import re
import io


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BMI Calculator",
    page_icon="⚖️",
    layout="centered"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #666;
    font-size: 18px;
    margin-bottom: 25px;
}

.result-box {
    padding: 25px;
    border-radius: 15px;
    border: 2px solid #ddd;
    text-align: center;
    margin-top: 20px;
}

.bmi-number {
    font-size: 48px;
    font-weight: bold;
}

.category {
    font-size: 25px;
    font-weight: bold;
    margin-bottom: 20px;
}

.result-item {
    padding: 12px;
    margin: 8px 0;
    border-radius: 10px;
    border: 1px solid #ddd;
    font-size: 17px;
}

.result-value {
    font-size: 22px;
    font-weight: bold;
}

.section-title {
    font-size: 22px;
    font-weight: bold;
}

.small-note {
    font-size: 13px;
    color: #666;
}

.auto-box {
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #ddd;
    margin-top: 10px;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DEFAULT VALUES
# ============================================================

DEFAULT_SEX = "Male"
DEFAULT_AGE = 25

DEFAULT_HEIGHT_CM = 170.0
DEFAULT_HEIGHT_FEET = 5
DEFAULT_HEIGHT_INCHES = 7.0

DEFAULT_WEIGHT_KG = 70.0
DEFAULT_WEIGHT_LB = 154.3

DEFAULT_HEIGHT_UNIT = "Centimeters (cm)"
DEFAULT_WEIGHT_UNIT = "Kilograms (kg)"


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "sex" not in st.session_state:
    st.session_state.sex = DEFAULT_SEX

if "age" not in st.session_state:
    st.session_state.age = DEFAULT_AGE

if "height_cm" not in st.session_state:
    st.session_state.height_cm = DEFAULT_HEIGHT_CM

if "height_feet" not in st.session_state:
    st.session_state.height_feet = DEFAULT_HEIGHT_FEET

if "height_inches" not in st.session_state:
    st.session_state.height_inches = DEFAULT_HEIGHT_INCHES

if "weight_kg" not in st.session_state:
    st.session_state.weight_kg = DEFAULT_WEIGHT_KG

if "weight_lb" not in st.session_state:
    st.session_state.weight_lb = DEFAULT_WEIGHT_LB

if "height_unit" not in st.session_state:
    st.session_state.height_unit = DEFAULT_HEIGHT_UNIT

if "weight_unit" not in st.session_state:
    st.session_state.weight_unit = DEFAULT_WEIGHT_UNIT

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""

if "ocr_sex" not in st.session_state:
    st.session_state.ocr_sex = None

if "ocr_age" not in st.session_state:
    st.session_state.ocr_age = None

if "ocr_height" not in st.session_state:
    st.session_state.ocr_height = None

if "ocr_weight" not in st.session_state:
    st.session_state.ocr_weight = None

if "bmi_result" not in st.session_state:
    st.session_state.bmi_result = None

if "bmi_category" not in st.session_state:
    st.session_state.bmi_category = None

if "calories_result" not in st.session_state:
    st.session_state.calories_result = None

if "ideal_weight" not in st.session_state:
    st.session_state.ideal_weight = None

if "healthy_weight_min" not in st.session_state:
    st.session_state.healthy_weight_min = None

if "healthy_weight_max" not in st.session_state:
    st.session_state.healthy_weight_max = None

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


# ============================================================
# RESET FUNCTION
# IMPORTANT:
# This function is used as an on_click callback.
# This prevents StreamlitWidgetAlreadyInstantiatedError.
# ============================================================

def reset_application():

    # Reset normal form values
    st.session_state.sex = DEFAULT_SEX
    st.session_state.age = DEFAULT_AGE

    st.session_state.height_cm = DEFAULT_HEIGHT_CM
    st.session_state.height_feet = DEFAULT_HEIGHT_FEET
    st.session_state.height_inches = DEFAULT_HEIGHT_INCHES

    st.session_state.weight_kg = DEFAULT_WEIGHT_KG
    st.session_state.weight_lb = DEFAULT_WEIGHT_LB

    st.session_state.height_unit = DEFAULT_HEIGHT_UNIT
    st.session_state.weight_unit = DEFAULT_WEIGHT_UNIT

    # Reset uploaded photo
    st.session_state.uploaded_image = None

    # Reset OCR
    st.session_state.ocr_text = ""
    st.session_state.ocr_sex = None
    st.session_state.ocr_age = None
    st.session_state.ocr_height = None
    st.session_state.ocr_weight = None

    # Reset results
    st.session_state.bmi_result = None
    st.session_state.bmi_category = None
    st.session_state.calories_result = None

    # Reset weight calculations
    st.session_state.ideal_weight = None
    st.session_state.healthy_weight_min = None
    st.session_state.healthy_weight_max = None

    # Change uploader key so uploaded photo disappears
    st.session_state.uploader_key += 1


# ============================================================
# CONVERSION FUNCTIONS
# ============================================================

def pounds_to_kg(pounds):
    return pounds * 0.45359237


def kg_to_pounds(kg):
    return kg / 0.45359237


def feet_inches_to_cm(feet, inches):
    return (feet * 30.48) + (inches * 2.54)


# ============================================================
# BMI
# ============================================================

def calculate_bmi(weight_kg, height_cm):

    if weight_kg <= 0 or height_cm <= 0:
        return None

    height_m = height_cm / 100

    bmi = weight_kg / (height_m ** 2)

    return round(bmi, 1)


# ============================================================
# BMI CATEGORY
# ============================================================

def get_category(bmi):

    if bmi < 18.5:
        return "Underweight"

    elif bmi < 25:
        return "Normal weight"

    elif bmi < 30:
        return "Overweight"

    else:
        return "Obesity"


# ============================================================
# HEALTHY / IDEAL WEIGHT
# ============================================================

def calculate_healthy_weight_range(height_cm):

    """
    Healthy BMI range:
        18.5 - 24.9

    Weight = BMI × height(m)^2

    Ideal weight:
        Uses BMI 21.7 as the midpoint/reference value.
    """

    if height_cm <= 0:
        return None, None, None

    height_m = height_cm / 100

    healthy_min = 18.5 * (height_m ** 2)
    healthy_max = 24.9 * (height_m ** 2)

    # Reference/ideal weight based on BMI 21.7
    ideal = 21.7 * (height_m ** 2)

    return (
        round(ideal, 1),
        round(healthy_min, 1),
        round(healthy_max, 1)
    )


# ============================================================
# CALORIES
# ============================================================

def calculate_bmr(sex, age, weight_kg, height_cm):

    if sex == "Male":

        return (
            10 * weight_kg
            + 6.25 * height_cm
            - 5 * age
            + 5
        )

    else:

        return (
            10 * weight_kg
            + 6.25 * height_cm
            - 5 * age
            - 161
        )


def calculate_calories(
    sex,
    age,
    weight_kg,
    height_cm
):

    bmr = calculate_bmr(
        sex,
        age,
        weight_kg,
        height_cm
    )

    # Basic sedentary estimate
    calories = bmr * 1.2

    return round(calories)


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image):

    image = image.convert("RGB")

    width, height = image.size

    # Enlarge small photos
    if width < 1800:

        scale = 1800 / width

        image = image.resize(
            (
                int(width * scale),
                int(height * scale)
            )
        )

    # Grayscale
    gray = ImageOps.grayscale(image)

    # Increase contrast
    gray = ImageEnhance.Contrast(gray).enhance(3.0)

    # Sharpen
    gray = ImageEnhance.Sharpness(gray).enhance(2.5)

    # Additional sharpening
    gray = gray.filter(
        ImageFilter.SHARPEN
    )

    return gray


# ============================================================
# OCR EXTRACTION
# ============================================================

def extract_information(text):

    # Normalize OCR text
    text_clean = re.sub(
        r"[|]",
        " ",
        text
    )

    text_lower = text_clean.lower()

    sex = None
    age = None
    height = None
    weight = None


    # ========================================================
    # SEX
    # ========================================================

    if re.search(
        r"\b(male|man|boy|m)\b",
        text_lower
    ):

        sex = "Male"

    elif re.search(
        r"\b(female|woman|girl|f)\b",
        text_lower
    ):

        sex = "Female"


    # ========================================================
    # AGE
    # ========================================================

    age_patterns = [

        r"(?:age|a9e|agc)\s*[:=\-]?\s*(\d{1,3})",

        r"(\d{1,3})\s*(?:years?|yrs?)\s*(?:old)?",

        r"(?:years?|yrs?)\s*[:=\-]?\s*(\d{1,3})"

    ]

    for pattern in age_patterns:

        match = re.search(
            pattern,
            text_lower
        )

        if match:

            try:

                value = int(
                    match.group(1)
                )

                if 1 <= value <= 120:

                    age = value
                    break

            except:
                pass


    # ========================================================
    # WEIGHT KG
    # ========================================================

    weight_kg_patterns = [

        r"(?:weight|wt|w)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms?)",

        r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms?)"

    ]

    for pattern in weight_kg_patterns:

        match = re.search(
            pattern,
            text_lower
        )

        if match:

            try:

                value = float(
                    match.group(1)
                )

                if 10 <= value <= 300:

                    weight = round(
                        value,
                        1
                    )

                    break

            except:
                pass


    # ========================================================
    # WEIGHT POUNDS
    # ========================================================

    if weight is None:

        weight_lb_patterns = [

            r"(?:weight|wt|w)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)",

            r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)"

        ]

        for pattern in weight_lb_patterns:

            match = re.search(
                pattern,
                text_lower
            )

            if match:

                try:

                    value = float(
                        match.group(1)
                    )

                    if 22 <= value <= 660:

                        weight = round(
                            pounds_to_kg(value),
                            1
                        )

                        break

                except:
                    pass


    # ========================================================
    # HEIGHT CM
    # ========================================================

    height_cm_patterns = [

        r"(?:height|ht|h)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(?:cm|centimeters?)",

        r"(\d+(?:\.\d+)?)\s*(?:cm|centimeters?)"

    ]

    for pattern in height_cm_patterns:

        match = re.search(
            pattern,
            text_lower
        )

        if match:

            try:

                value = float(
                    match.group(1)
                )

                if 50 <= value <= 250:

                    height = round(
                        value,
                        1
                    )

                    break

            except:
                pass


    # ========================================================
    # HEIGHT FEET + INCHES
    # ========================================================

    if height is None:

        feet_patterns = [

            r"(?:height|ht|h)\s*[:=\-]?\s*(\d+)\s*(?:ft|feet|foot)\s*(\d+(?:\.\d+)?)?\s*(?:in|inch|inches)?",

            r"(\d+)\s*(?:ft|feet|foot)\s*(\d+(?:\.\d+)?)?\s*(?:in|inch|inches)?"

        ]

        for pattern in feet_patterns:

            match = re.search(
                pattern,
                text_lower
            )

            if match:

                try:

                    feet = float(
                        match.group(1)
                    )

                    inches = (
                        float(match.group(2))
                        if match.group(2)
                        else 0
                    )

                    value = feet_inches_to_cm(
                        feet,
                        inches
                    )

                    if 50 <= value <= 250:

                        height = round(
                            value,
                            1
                        )

                        break

                except:
                    pass


    # ========================================================
    # HEIGHT METERS
    # ========================================================

    if height is None:

        meter_patterns = [

            r"(?:height|ht|h)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(?:m|meters?)",

            r"(\d+\.\d+)\s*m\b"

        ]

        for pattern in meter_patterns:

            match = re.search(
                pattern,
                text_lower
            )

            if match:

                try:

                    value = (
                        float(match.group(1))
                        * 100
                    )

                    if 50 <= value <= 250:

                        height = round(
                            value,
                            1
                        )

                        break

                except:
                    pass


    return (
        sex,
        age,
        height,
        weight
    )


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">⚖️ BMI Calculator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Calculate BMI and estimate daily calorie needs'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# PHOTO SECTION
# ============================================================

st.subheader("📷 1. Upload Photo")

uploaded_file = st.file_uploader(
    "Upload a photo containing height, weight, age or sex",
    type=["jpg", "jpeg", "png"],
    key=f"photo_uploader_{st.session_state.uploader_key}"
)


# ============================================================
# PROCESS PHOTO
# ============================================================

if uploaded_file is not None:

    image_bytes = uploaded_file.getvalue()

    image = Image.open(
        io.BytesIO(image_bytes)
    )

    st.session_state.uploaded_image = image_bytes

    st.image(
        image,
        caption="Uploaded Photo",
        use_container_width=True
    )


    # --------------------------------------------------------
    # EXTRACT BUTTON
    # --------------------------------------------------------

    if st.button(
        "🔍 Extract Information",
        use_container_width=True
    ):

        with st.spinner(
            "🔍 Reading information from photo..."
        ):

            processed_image = preprocess_image(
                image
            )

            text = pytesseract.image_to_string(
                processed_image,
                config="--psm 6"
            )

            (
                detected_sex,
                detected_age,
                detected_height,
                detected_weight
            ) = extract_information(text)


            # Save extracted information

            st.session_state.ocr_text = text

            st.session_state.ocr_sex = (
                detected_sex
            )

            st.session_state.ocr_age = (
                detected_age
            )

            st.session_state.ocr_height = (
                detected_height
            )

            st.session_state.ocr_weight = (
                detected_weight
            )

        st.success(
            "✅ Information extracted successfully!"
        )


# ============================================================
# EXTRACTED INFORMATION
# ============================================================

if st.session_state.ocr_text:

    st.subheader(
        "📋 2. Extracted Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.session_state.ocr_sex:

            st.success(
                f"👤 Sex: "
                f"{st.session_state.ocr_sex}"
            )

        else:

            st.warning(
                "⚠️ Sex could not be detected."
            )


        if st.session_state.ocr_age:

            st.success(
                f"🎂 Age: "
                f"{st.session_state.ocr_age} years"
            )

        else:

            st.warning(
                "⚠️ Age could not be detected."
            )


    with col2:

        if st.session_state.ocr_height:

            st.success(
                f"📏 Height: "
                f"{st.session_state.ocr_height} cm"
            )

        else:

            st.warning(
                "⚠️ Height could not be detected."
            )


        if st.session_state.ocr_weight:

            st.success(
                f"⚖️ Weight: "
                f"{st.session_state.ocr_weight} kg"
            )

        else:

            st.warning(
                "⚠️ Weight could not be detected."
            )


    # --------------------------------------------------------
    # AUTO FILL BUTTON
    # --------------------------------------------------------

    st.markdown(
        '<div class="auto-box">',
        unsafe_allow_html=True
    )

    st.write(
        "🤖 **Automatically fill the form using the "
        "information extracted from the photo.**"
    )

    if st.button(
        "🤖 Auto Fill Form",
        type="primary",
        use_container_width=True
    ):

        filled = []

        # Sex
        if st.session_state.ocr_sex:

            st.session_state.sex = (
                st.session_state.ocr_sex
            )

            filled.append("Sex")


        # Age
        if st.session_state.ocr_age:

            st.session_state.age = (
                st.session_state.ocr_age
            )

            filled.append("Age")


        # Height
        if st.session_state.ocr_height:

            st.session_state.height_cm = (
                st.session_state.ocr_height
            )

            st.session_state.height_unit = (
                "Centimeters (cm)"
            )

            filled.append("Height")


        # Weight
        if st.session_state.ocr_weight:

            st.session_state.weight_kg = (
                st.session_state.ocr_weight
            )

            st.session_state.weight_unit = (
                "Kilograms (kg)"
            )

            filled.append("Weight")


        if filled:

            st.success(
                "✅ Auto-filled: "
                + ", ".join(filled)
            )

            st.rerun()

        else:

            st.error(
                "❌ No usable information was detected."
            )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # RAW OCR
    # --------------------------------------------------------

    with st.expander(
        "🔎 Show Raw Extracted Text"
    ):

        st.text(
            st.session_state.ocr_text
        )


# ============================================================
# MANUAL FORM
# ============================================================

st.divider()

st.subheader(
    "📝 3. BMI Information"
)


# ============================================================
# SEX + AGE
# ============================================================

col1, col2 = st.columns(2)

with col1:

    sex = st.selectbox(
        "👤 Sex",
        ["Male", "Female"],
        key="sex"
    )


with col2:

    age = st.number_input(
        "🎂 Age (years)",
        min_value=1,
        max_value=120,
        step=1,
        key="age"
    )


# ============================================================
# HEIGHT
# ============================================================

st.markdown("### 📏 Height")

height_unit = st.radio(
    "Select height unit",
    [
        "Centimeters (cm)",
        "Feet & Inches"
    ],
    horizontal=True,
    key="height_unit"
)


if height_unit == "Centimeters (cm)":

    height_cm = st.number_input(
        "Height (cm)",
        min_value=50.0,
        max_value=250.0,
        step=0.1,
        key="height_cm"
    )

else:

    col1, col2 = st.columns(2)

    with col1:

        height_feet = st.number_input(
            "Feet",
            min_value=1,
            max_value=8,
            step=1,
            key="height_feet"
        )

    with col2:

        height_inches = st.number_input(
            "Inches",
            min_value=0.0,
            max_value=11.9,
            step=0.1,
            key="height_inches"
        )


    height_cm = feet_inches_to_cm(
        height_feet,
        height_inches
    )

    st.info(
        f"Equivalent height: "
        f"{height_cm:.1f} cm"
    )


# ============================================================
# WEIGHT
# ============================================================

st.markdown("### ⚖️ Weight")

weight_unit = st.radio(
    "Select weight unit",
    [
        "Kilograms (kg)",
        "Pounds (lb)"
    ],
    horizontal=True,
    key="weight_unit"
)


if weight_unit == "Kilograms (kg)":

    weight_kg = st.number_input(
        "Weight (kg)",
        min_value=10.0,
        max_value=300.0,
        step=0.1,
        key="weight_kg"
    )

else:

    weight_lb = st.number_input(
        "Weight (lb)",
        min_value=22.0,
        max_value=660.0,
        step=0.1,
        key="weight_lb"
    )

    weight_kg = pounds_to_kg(
        weight_lb
    )

    st.info(
        f"Equivalent weight: "
        f"{weight_kg:.1f} kg"
    )


# ============================================================
# CALCULATE
# ============================================================

st.divider()

if st.button(
    "🧮 Calculate BMI",
    type="primary",
    use_container_width=True
):

    # Validation

    if height_cm <= 0:

        st.error(
            "❌ Please enter a valid height."
        )

    elif weight_kg <= 0:

        st.error(
            "❌ Please enter a valid weight."
        )

    elif age <= 0:

        st.error(
            "❌ Please enter a valid age."
        )

    else:

        # -----------------------------------------------
        # BMI
        # -----------------------------------------------

        bmi = calculate_bmi(
            weight_kg,
            height_cm
        )

        category = get_category(
            bmi
        )


        # -----------------------------------------------
        # CALORIES
        # -----------------------------------------------

        calories = calculate_calories(
            sex,
            age,
            weight_kg,
            height_cm
        )


        # -----------------------------------------------
        # IDEAL / HEALTHY WEIGHT
        # -----------------------------------------------

        (
            ideal_weight,
            healthy_min,
            healthy_max
        ) = calculate_healthy_weight_range(
            height_cm
        )


        # -----------------------------------------------
        # SAVE RESULTS
        # -----------------------------------------------

        st.session_state.bmi_result = bmi

        st.session_state.bmi_category = (
            category
        )

        st.session_state.calories_result = (
            calories
        )

        st.session_state.ideal_weight = (
            ideal_weight
        )

        st.session_state.healthy_weight_min = (
            healthy_min
        )

        st.session_state.healthy_weight_max = (
            healthy_max
        )


# ============================================================
# RESULTS
# ============================================================

if st.session_state.bmi_result is not None:

    bmi = st.session_state.bmi_result

    category = (
        st.session_state.bmi_category
    )

    calories = (
        st.session_state.calories_result
    )

    ideal_weight = (
        st.session_state.ideal_weight
    )

    healthy_min = (
        st.session_state.healthy_weight_min
    )

    healthy_max = (
        st.session_state.healthy_weight_max
    )


    # ========================================================
    # RESULT TITLE
    # ========================================================

    st.subheader(
        "📊 4. Your Result"
    )


    # ========================================================
    # MAIN RESULT BOX
    # ========================================================

    st.markdown(
        f"""
        <div class="result-box">

            <div class="bmi-number">
                {bmi}
            </div>

            <div class="category">
                {category}
            </div>

            <div class="result-item">

                <div>
                    🎯 <strong>Ideal Weight</strong>
                </div>

                <div class="result-value">
                    {ideal_weight:.1f} kg
                </div>

            </div>

            <div class="result-item">

                <div>
                    ⚖️ <strong>Standard / Healthy Weight Range</strong>
                </div>

                <div class="result-value">
                    {healthy_min:.1f} – {healthy_max:.1f} kg
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # CALORIE RESULT
    # ========================================================

    st.markdown(
        "### 🔥 Estimated Daily Calories"
    )

    st.metric(
        "Estimated maintenance calories",
        f"{calories:,} kcal/day"
    )

    st.caption(
        "Basic estimate using the Mifflin-St Jeor "
        "equation and a sedentary activity factor."
    )


    # ========================================================
    # WEIGHT INFORMATION
    # ========================================================

    st.info(
        f"📏 Based on your height of "
        f"{height_cm:.1f} cm, a BMI of 18.5–24.9 "
        f"corresponds to a healthy weight range of "
        f"{healthy_min:.1f}–{healthy_max:.1f} kg. "
        f"The displayed ideal weight is a reference "
        f"point based on BMI 21.7."
    )


# ============================================================
# BMI REFERENCE
# ============================================================

st.divider()

st.subheader(
    "📚 BMI Reference"
)

st.markdown("""
| BMI | Category |
|---|---|
| Below 18.5 | Underweight |
| 18.5 – 24.9 | Normal weight |
| 25.0 – 29.9 | Overweight |
| 30.0 or above | Obesity |
""")


# ============================================================
# RESET
# IMPORTANT:
# Use on_click instead of:
#
# if st.button("Reset"):
#     reset_application()
#
# This prevents:
# StreamlitWidgetAlreadyInstantiatedError
# ============================================================

st.divider()

st.subheader(
    "🔄 Start Again"
)

st.button(
    "🔄 Reset",
    use_container_width=True,
    on_click=reset_application
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="small-note">
    ⚠️ Educational calculator only.
    OCR results should always be checked before use.
    BMI and calorie values are estimates and are not
    a medical diagnosis.
    </div>
    """,
    unsafe_allow_html=True
)
'''


with open(
    "/content/app.py",
    "w",
    encoding="utf-8"
) as f:

    f.write(app_code)

print("✅ app.py created successfully.")


# ============================================================
# 5. STOP OLD PROCESSES
# ============================================================

print()
print("🧹 Cleaning old processes...")

subprocess.run(
    ["pkill", "-9", "-f", "streamlit"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

subprocess.run(
    ["pkill", "-9", "-f", "cloudflared"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(3)


# ============================================================
# 6. START STREAMLIT
# ============================================================

print("🚀 Starting Streamlit...")

streamlit_log_path = "/content/streamlit.log"

streamlit_log = open(
    streamlit_log_path,
    "w"
)

streamlit_process = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "/content/app.py",

        "--server.address=0.0.0.0",

        "--server.port=8501",

        "--server.headless=true",

        "--browser.gatherUsageStats=false"
    ],

    stdout=streamlit_log,

    stderr=subprocess.STDOUT
)


# ============================================================
# 7. WAIT FOR STREAMLIT
# ============================================================

print("⏳ Waiting for Streamlit...")

streamlit_ready = False

for i in range(30):

    time.sleep(1)

    try:

        response = urllib.request.urlopen(
            "http://127.0.0.1:8501",
            timeout=2
        )

        if response.status == 200:

            streamlit_ready = True
            break

    except:
        pass


if streamlit_ready:

    print("✅ Streamlit is running!")

else:

    print("❌ Streamlit failed to start.")

    try:

        with open(
            streamlit_log_path,
            "r",
            errors="ignore"
        ) as f:

            print(
                f.read()[-8000:]
            )

    except:
        pass

    raise SystemExit


# ============================================================
# 8. START CLOUDFLARE
# ============================================================

print()
print("🌐 Starting Cloudflare Tunnel...")

cloudflare_log_path = (
    "/content/cloudflare.log"
)

cloudflare_log = open(
    cloudflare_log_path,
    "w"
)

cloudflare_process = subprocess.Popen(
    [
        "cloudflared",

        "tunnel",

        "--url",

        "http://127.0.0.1:8501",

        "--no-autoupdate"
    ],

    stdout=cloudflare_log,

    stderr=subprocess.STDOUT
)


# ============================================================
# 9. FIND CLOUDFLARE URL
# ============================================================

print(
    "⏳ Waiting for Cloudflare public URL..."
)

public_url = None

for i in range(90):

    time.sleep(1)

    try:

        with open(
            cloudflare_log_path,
            "r",
            errors="ignore"
        ) as f:

            log = f.read()


        matches = re.findall(
            r"https://[a-zA-Z0-9-]+\.trycloudflare\.com",
            log
        )


        if matches:

            public_url = matches[-1]

            break

    except:
        pass


    if i % 10 == 0:

        print(
            f"   Waiting... {i} seconds"
        )


# ============================================================
# 10. SHOW RESULT
# ============================================================

print()

if public_url:

    print("=" * 75)

    print(
        "🎉 BMI CALCULATOR IS READY!"
    )

    print("=" * 75)

    print()

    print(
        "🌐 PUBLIC URL:"
    )

    print()

    print(
        public_url
    )

    print()

    print("=" * 75)

    print(
        "✅ Features included:"
    )

    print(
        "   📷 Photo upload"
    )

    print(
        "   🔍 OCR information extraction"
    )

    print(
        "   🤖 Auto Fill Form"
    )

    print(
        "   🧮 BMI calculation"
    )

    print(
        "   🎯 Ideal weight"
    )

    print(
        "   ⚖️ Healthy weight range"
    )

    print(
        "   🔥 Calorie estimate"
    )

    print(
        "   🔄 Reset to defaults"
    )

    print()

    print("=" * 75)

    print(
        "⚠️ Keep this Colab session running."
    )

    print(
        "⚠️ The public URL will stop if the runtime stops."
    )

    print("=" * 75)

else:

    print(
        "❌ Cloudflare URL was not detected."
    )

    print()

    print(
        "Last Cloudflare log:"
    )

    print("-" * 75)

    try:

        with open(
            cloudflare_log_path,
            "r",
            errors="ignore"
        ) as f:

            print(
                f.read()[-10000:]
            )

    except Exception as e:

        print(
            "Could not read Cloudflare log:",
            e
        )
