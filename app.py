
import re
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="BMI Calculator",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# =========================================================
# DEFAULT VALUES
# =========================================================

DEFAULT_SEX = "Male"
DEFAULT_AGE = 25

DEFAULT_HEIGHT_CM = 170.0
DEFAULT_HEIGHT_FEET = 5
DEFAULT_HEIGHT_INCHES = 7.0

DEFAULT_WEIGHT_KG = 70.0
DEFAULT_WEIGHT_LB = 154.3

DEFAULT_HEIGHT_UNIT = "Centimeters (cm)"
DEFAULT_WEIGHT_UNIT = "Kilograms (kg)"


# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

defaults = {
    "sex": DEFAULT_SEX,
    "age": DEFAULT_AGE,

    "height_cm": DEFAULT_HEIGHT_CM,
    "height_feet": DEFAULT_HEIGHT_FEET,
    "height_inches": DEFAULT_HEIGHT_INCHES,

    "weight_kg": DEFAULT_WEIGHT_KG,
    "weight_lb": DEFAULT_WEIGHT_LB,

    "height_unit": DEFAULT_HEIGHT_UNIT,
    "weight_unit": DEFAULT_WEIGHT_UNIT,

    "uploaded_image": None,
    "ocr_text": "",

    "ocr_sex": None,
    "ocr_age": None,
    "ocr_height": None,
    "ocr_weight": None,

    "bmi_result": None,
    "bmi_category": None,

    "calories_result": None,

    "ideal_weight": None,
    "healthy_weight_min": None,
    "healthy_weight_max": None,

    "uploader_key": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# RESET FUNCTION
# =========================================================

def reset_application():
    """
    Reset the complete application to its default state.
    This function is used as a button callback so that
    widget-related session state is safely updated.
    """

    st.session_state.sex = DEFAULT_SEX
    st.session_state.age = DEFAULT_AGE

    st.session_state.height_cm = DEFAULT_HEIGHT_CM
    st.session_state.height_feet = DEFAULT_HEIGHT_FEET
    st.session_state.height_inches = DEFAULT_HEIGHT_INCHES

    st.session_state.weight_kg = DEFAULT_WEIGHT_KG
    st.session_state.weight_lb = DEFAULT_WEIGHT_LB

    st.session_state.height_unit = DEFAULT_HEIGHT_UNIT
    st.session_state.weight_unit = DEFAULT_WEIGHT_UNIT

    st.session_state.uploaded_image = None
    st.session_state.ocr_text = ""

    st.session_state.ocr_sex = None
    st.session_state.ocr_age = None
    st.session_state.ocr_height = None
    st.session_state.ocr_weight = None

    st.session_state.bmi_result = None
    st.session_state.bmi_category = None

    st.session_state.calories_result = None

    st.session_state.ideal_weight = None
    st.session_state.healthy_weight_min = None
    st.session_state.healthy_weight_max = None

    # Change uploader key so Streamlit clears uploaded file
    st.session_state.uploader_key += 1


# =========================================================
# CONVERSION FUNCTIONS
# =========================================================

def pounds_to_kg(pounds):
    return pounds * 0.45359237


def kg_to_pounds(kg):
    return kg / 0.45359237


def feet_inches_to_cm(feet, inches):
    return (feet * 30.48) + (inches * 2.54)


# =========================================================
# BMI CALCULATION
# =========================================================

def calculate_bmi(weight_kg, height_cm):

    if weight_kg <= 0 or height_cm <= 0:
        return None

    height_m = height_cm / 100

    bmi = weight_kg / (height_m ** 2)

    return round(bmi, 1)


def get_category(bmi):

    if bmi < 18.5:
        return "Underweight"

    elif bmi < 25:
        return "Normal weight"

    elif bmi < 30:
        return "Overweight"

    else:
        return "Obesity"


# =========================================================
# HEALTHY / IDEAL WEIGHT
# =========================================================

def calculate_healthy_weight_range(height_cm):

    if height_cm <= 0:
        return None, None, None

    height_m = height_cm / 100

    healthy_min = 18.5 * (height_m ** 2)
    healthy_max = 24.9 * (height_m ** 2)

    # Reference point using BMI 21.7
    ideal = 21.7 * (height_m ** 2)

    return (
        round(ideal, 1),
        round(healthy_min, 1),
        round(healthy_max, 1)
    )


# =========================================================
# CALORIE CALCULATION
# =========================================================

def calculate_bmr(sex, age, weight_kg, height_cm):

    if sex == "Male":

        bmr = (
            10 * weight_kg
            + 6.25 * height_cm
            - 5 * age
            + 5
        )

    else:

        bmr = (
            10 * weight_kg
            + 6.25 * height_cm
            - 5 * age
            - 161
        )

    return bmr


def calculate_calories(sex, age, weight_kg, height_cm):

    bmr = calculate_bmr(
        sex,
        age,
        weight_kg,
        height_cm
    )

    # Sedentary activity estimate
    calories = bmr * 1.2

    return round(calories)


# =========================================================
# OCR IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image):

    image = image.convert("RGB")

    width, height = image.size

    # Increase small images for better OCR
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

    # Increase sharpness
    gray = ImageEnhance.Sharpness(gray).enhance(2.5)

    gray = gray.filter(ImageFilter.SHARPEN)

    return gray


# =========================================================
# OCR EXTRACTION
# =========================================================

def extract_information(image):

    processed = preprocess_image(image)

    text = pytesseract.image_to_string(
        processed,
        config="--psm 6"
    )

    text = text.replace("|", "I")

    return text


# =========================================================
# SEX EXTRACTION
# =========================================================

def extract_sex(text):

    lower_text = text.lower()

    female_patterns = [
        r"\bfemale\b",
        r"\bwoman\b",
        r"\bgirl\b",
        r"\bf\b"
    ]

    male_patterns = [
        r"\bmale\b",
        r"\bman\b",
        r"\bboy\b",
        r"\bm\b"
    ]

    for pattern in female_patterns:

        if re.search(pattern, lower_text):
            return "Female"

    for pattern in male_patterns:

        if re.search(pattern, lower_text):
            return "Male"

    return None


# =========================================================
# AGE EXTRACTION
# =========================================================

def extract_age(text):

    patterns = [

        r"(?:age|a9e|agc)\s*[:=\-]?\s*(\d{1,3})",

        r"(\d{1,3})\s*(?:years?|yrs?)\s*(?:old)?",

        r"(?:years?|yrs?)\s*[:=\-]?\s*(\d{1,3})"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            age = int(match.group(1))

            if 1 <= age <= 120:
                return age

    return None


# =========================================================
# WEIGHT EXTRACTION
# =========================================================

def extract_weight(text):

    # Weight in kilograms
    kg_patterns = [

        r"(?:weight|wt|w)\s*[:=\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:kg|kgs|kilograms?)",

        r"(\d+(?:\.\d+)?)\s*"
        r"(?:kg|kgs|kilograms?)"
    ]

    for pattern in kg_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for value in matches:

            weight = float(value)

            if 10 <= weight <= 300:
                return round(weight, 1)

    # Weight in pounds
    lb_patterns = [

        r"(?:weight|wt|w)\s*[:=\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:lb|lbs|pounds?)",

        r"(\d+(?:\.\d+)?)\s*"
        r"(?:lb|lbs|pounds?)"
    ]

    for pattern in lb_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for value in matches:

            pounds = float(value)

            if 22 <= pounds <= 660:

                return round(
                    pounds_to_kg(pounds),
                    1
                )

    return None


# =========================================================
# HEIGHT EXTRACTION
# =========================================================

def extract_height(text):

    # Height in centimeters
    cm_patterns = [

        r"(?:height|ht|h)\s*[:=\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:cm|cms|centimeters?)",

        r"(\d+(?:\.\d+)?)\s*"
        r"(?:cm|cms|centimeters?)"
    ]

    for pattern in cm_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for value in matches:

            height = float(value)

            if 50 <= height <= 250:
                return round(height, 1)

    # Feet and inches
    ft_in_patterns = [

        r"(\d{1,2})\s*(?:ft|feet|foot)"
        r"\s*(?:and)?\s*"
        r"(\d{1,2}(?:\.\d+)?)\s*"
        r"(?:in|inch|inches)",

        r"(\d{1,2})\s*['’]"
        r"\s*(\d{1,2}(?:\.\d+)?)\s*[\"”]"
    ]

    for pattern in ft_in_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            feet = int(match.group(1))
            inches = float(match.group(2))

            if 2 <= feet <= 8 and 0 <= inches < 12:

                height = feet_inches_to_cm(
                    feet,
                    inches
                )

                return round(height, 1)

    # Height in meters
    meter_patterns = [

        r"(?:height|ht|h)\s*[:=\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:m|meter|meters)",

        r"(\d+\.\d+)\s*"
        r"(?:m|meter|meters)"
    ]

    for pattern in meter_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for value in matches:

            meters = float(value)

            if 0.5 <= meters <= 2.5:

                return round(
                    meters * 100,
                    1
                )

    return None


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 17px;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 750;
        margin-top: 25px;
        margin-bottom: 12px;
    }

    .result-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 28px;
        margin-top: 20px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
    }

    .result-title {
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }

    .bmi-number {
        font-size: 58px;
        font-weight: 800;
        line-height: 1.1;
        margin: 5px 0 10px 0;
    }

    .category {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 25px;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 25px;
        background: #e8f5e9;
    }

    .result-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        text-align: left;
    }

    .result-item {
        display: flex;
        align-items: center;
        gap: 14px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px;
    }

    .result-icon {
        font-size: 28px;
        min-width: 35px;
    }

    .result-content {
        flex: 1;
    }

    .result-label {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 5px;
    }

    .result-value {
        font-size: 19px;
        font-weight: 800;
    }

    .info-card {
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .footer {
        text-align: center;
        font-size: 13px;
        margin-top: 35px;
        padding-top: 20px;
    }

    @media (max-width: 700px) {

        .result-details {
            grid-template-columns: 1fr;
        }

        .bmi-number {
            font-size: 48px;
        }

        .result-box {
            padding: 20px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">⚖️ BMI Calculator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Calculate BMI, estimate daily calorie needs, and check healthy weight range'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# PHOTO OCR SECTION
# =========================================================

st.markdown(
    '<div class="section-title">📷 Upload Photo for Automatic Extraction</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload a photo containing health information",
    type=["jpg", "jpeg", "png"],
    key=f"photo_uploader_{st.session_state.uploader_key}"
)


if uploaded_file is not None:

    image = Image.open(uploaded_file)

    st.session_state.uploaded_image = image

    st.image(
        image,
        caption="Uploaded Image",
        use_container_width=True
    )

    if st.button(
        "🔍 Extract Information",
        use_container_width=True
    ):

        with st.spinner("Reading information from the image..."):

            try:

                text = extract_information(image)

                st.session_state.ocr_text = text

                st.session_state.ocr_sex = extract_sex(text)
                st.session_state.ocr_age = extract_age(text)
                st.session_state.ocr_height = extract_height(text)
                st.session_state.ocr_weight = extract_weight(text)

                st.success(
                    "Information extraction completed."
                )

            except Exception as e:

                st.error(
                    f"Could not process the image: {e}"
                )


# =========================================================
# EXTRACTED INFORMATION
# =========================================================

if st.session_state.ocr_text:

    st.markdown(
        '<div class="section-title">📋 Extracted Information</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.session_state.ocr_sex:

            st.success(
                f"Sex: {st.session_state.ocr_sex}"
            )

        else:

            st.warning("Sex could not be detected.")

        if st.session_state.ocr_height:

            st.success(
                f"Height: {st.session_state.ocr_height:.1f} cm"
            )

        else:

            st.warning(
                "Height could not be detected."
            )

    with col2:

        if st.session_state.ocr_age:

            st.success(
                f"Age: {st.session_state.ocr_age}"
            )

        else:

            st.warning(
                "Age could not be detected."
            )

        if st.session_state.ocr_weight:

            st.success(
                f"Weight: {st.session_state.ocr_weight:.1f} kg"
            )

        else:

            st.warning(
                "Weight could not be detected."
            )

    # -----------------------------------------------------
    # AUTO FILL
    # -----------------------------------------------------

    if st.button(
        "🤖 Auto Fill Form",
        use_container_width=True
    ):

        if st.session_state.ocr_sex is not None:

            st.session_state.sex = (
                st.session_state.ocr_sex
            )

        if st.session_state.ocr_age is not None:

            st.session_state.age = (
                st.session_state.ocr_age
            )

        if st.session_state.ocr_height is not None:

            st.session_state.height_cm = (
                st.session_state.ocr_height
            )

            st.session_state.height_unit = (
                "Centimeters (cm)"
            )

        if st.session_state.ocr_weight is not None:

            st.session_state.weight_kg = (
                st.session_state.ocr_weight
            )

            st.session_state.weight_lb = (
                kg_to_pounds(
                    st.session_state.ocr_weight
                )
            )

            st.session_state.weight_unit = (
                "Kilograms (kg)"
            )

        st.success(
            "Information automatically filled into the form."
        )

        st.rerun()

    # -----------------------------------------------------
    # RAW OCR TEXT
    # -----------------------------------------------------

    with st.expander("🔎 View Raw Extracted Text"):

        st.text(
            st.session_state.ocr_text
        )


# =========================================================
# MANUAL INFORMATION
# =========================================================

st.markdown(
    '<div class="section-title">📝 BMI Information</div>',
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# SEX
# ---------------------------------------------------------

sex = st.selectbox(
    "Sex",
    ["Male", "Female"],
    key="sex"
)


# ---------------------------------------------------------
# AGE
# ---------------------------------------------------------

age = st.number_input(
    "Age",
    min_value=1,
    max_value=120,
    step=1,
    key="age"
)


# =========================================================
# HEIGHT
# =========================================================

height_unit = st.radio(
    "Height Unit",
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
            min_value=2,
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


# =========================================================
# WEIGHT
# =========================================================

weight_unit = st.radio(
    "Weight Unit",
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


# =========================================================
# CALCULATE BMI BUTTON
# =========================================================

if st.button(
    "📊 Calculate BMI",
    use_container_width=True
):

    if age <= 0:

        st.error(
            "Please enter a valid age."
        )

    elif height_cm <= 0:

        st.error(
            "Please enter a valid height."
        )

    elif weight_kg <= 0:

        st.error(
            "Please enter a valid weight."
        )

    else:

        bmi = calculate_bmi(
            weight_kg,
            height_cm
        )

        category = get_category(bmi)

        ideal_weight, healthy_min, healthy_max = (
            calculate_healthy_weight_range(
                height_cm
            )
        )

        calories = calculate_calories(
            sex,
            age,
            weight_kg,
            height_cm
        )

        st.session_state.bmi_result = bmi
        st.session_state.bmi_category = category

        st.session_state.ideal_weight = ideal_weight
        st.session_state.healthy_weight_min = healthy_min
        st.session_state.healthy_weight_max = healthy_max

        st.session_state.calories_result = calories


# =========================================================
# RESULT BOX
# =========================================================

if st.session_state.bmi_result is not None:

    bmi = st.session_state.bmi_result
    category = st.session_state.bmi_category

    ideal_weight = st.session_state.ideal_weight
    healthy_min = st.session_state.healthy_weight_min
    healthy_max = st.session_state.healthy_weight_max

    st.markdown(
        '<div class="section-title">📊 Your Result</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="result-box">

            <div class="result-title">
                YOUR BMI
            </div>

            <div class="bmi-number">
                {bmi:.1f}
            </div>

            <div class="category">
                {category}
            </div>

            <div class="result-details">

                <div class="result-item">

                    <div class="result-icon">
                        🎯
                    </div>

                    <div class="result-content">

                        <div class="result-label">
                            Ideal Weight
                        </div>

                        <div class="result-value">
                            {ideal_weight:.1f} kg
                        </div>

                    </div>

                </div>


                <div class="result-item">

                    <div class="result-icon">
                        ⚖️
                    </div>

                    <div class="result-content">

                        <div class="result-label">
                            Healthy Weight Range
                        </div>

                        <div class="result-value">
                            {healthy_min:.1f} – {healthy_max:.1f} kg
                        </div>

                    </div>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # =====================================================
    # CALORIES
    # =====================================================

    if st.session_state.calories_result is not None:

        st.markdown(
            '<div class="section-title">🔥 Estimated Daily Calories</div>',
            unsafe_allow_html=True
        )

        st.info(
            f"Estimated maintenance calories: "
            f"**{st.session_state.calories_result:,} kcal/day**"
        )

        st.caption(
            "This estimate uses the Mifflin-St Jeor equation "
            "with a sedentary activity factor of 1.2."
        )


    # =====================================================
    # BMI REFERENCE
    # =====================================================

    st.markdown(
        '<div class="section-title">📚 BMI Reference</div>',
        unsafe_allow_html=True
    )

    st.table(
        {
            "BMI": [
                "Below 18.5",
                "18.5 – 24.9",
                "25.0 – 29.9",
                "30.0 and above"
            ],

            "Category": [
                "Underweight",
                "Normal weight",
                "Overweight",
                "Obesity"
            ]
        }
    )


# =========================================================
# RESET BUTTON
# =========================================================

st.markdown("---")

st.button(
    "🔄 Reset",
    use_container_width=True,
    on_click=reset_application
)


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        BMI Calculator • Photo OCR • Auto Fill • Calorie Estimate
        <br><br>
        <small>
        This calculator provides general estimates for educational purposes
        and is not a substitute for professional medical advice.
        </small>
    </div>
    """,
    unsafe_allow_html=True
)

