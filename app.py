#`python
import io
import re

import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BMI Calculator",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)


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
# SESSION STATE
# ============================================================

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

    "uploader_key": 0
}


for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# RESET
# ============================================================

def reset_application():

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

    st.session_state.uploader_key += 1


# ============================================================
# CONVERSIONS
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


def get_category(bmi):

    if bmi < 18.5:
        return "Underweight"

    elif bmi < 25:
        return "Normal weight"

    elif bmi < 30:
        return "Overweight"

    return "Obesity"


# ============================================================
# HEALTHY / IDEAL WEIGHT
# ============================================================

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


# ============================================================
# BMR / CALORIES
# ============================================================

def calculate_bmr(sex, age, weight_kg, height_cm):

    if sex == "Male":

        return (
            10 * weight_kg
            + 6.25 * height_cm
            - 5 * age
            + 5
        )

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

    # Sedentary activity factor
    calories = bmr * 1.2

    return round(calories)


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image):

    image = image.convert("RGB")

    width, height = image.size

    # Enlarge smaller images
    if width < 1800:

        scale = 1800 / width

        image = image.resize(
            (
                int(width * scale),
                int(height * scale)
            )
        )

    gray = ImageOps.grayscale(image)

    gray = ImageEnhance.Contrast(
        gray
    ).enhance(3.0)

    gray = ImageEnhance.Sharpness(
        gray
    ).enhance(2.5)

    gray = gray.filter(
        ImageFilter.SHARPEN
    )

    return gray


# ============================================================
# OCR EXTRACTION
# ============================================================

def extract_information(text):

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

    female_match = re.search(
        r"\b(female|woman|girl)\b",
        text_lower
    )

    male_match = re.search(
        r"\b(male|man|boy)\b",
        text_lower
    )

    if female_match:

        sex = "Female"

    elif male_match:

        sex = "Male"

    else:

        if re.search(
            r"(?:sex|gender)\s*[:=\-]?\s*f\b",
            text_lower
        ):

            sex = "Female"

        elif re.search(
            r"(?:sex|gender)\s*[:=\-]?\s*m\b",
            text_lower
        ):

            sex = "Male"


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

            except (ValueError, TypeError):

                pass


    # ========================================================
    # WEIGHT - KG
    # ========================================================

    weight_kg_patterns = [

        r"(?:weight|wt)\s*[:=\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:kg|kgs|kilograms?)",

        r"(\d+(?:\.\d+)?)\s*"
        r"(?:kg|kgs|kilograms?)"
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

            except (ValueError, TypeError):

                pass


    # ========================================================
    # WEIGHT - POUNDS
    # ========================================================

    if weight is None:

        weight_lb_patterns = [

            r"(?:weight|wt)\s*[:=\-]?\s*"
            r"(\d+(?:\.\d+)?)\s*"
            r"(?:lb|lbs|pounds?)",

            r"(\d+(?:\.\d+)?)\s*"
            r"(?:lb|lbs|pounds?)"
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

                except (ValueError, TypeError):

                    pass


    # ========================================================
    # HEIGHT - CM
    # ========================================================

    height_cm_patterns = [

        r"(?:height|ht)\s*[:=\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:cm|cms|centimeters?)",

        r"(\d+(?:\.\d+)?)\s*"
        r"(?:cm|cms|centimeters?)"
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

            except (ValueError, TypeError):

                pass


    # ========================================================
    # HEIGHT - FEET / INCHES
    # ========================================================

    if height is None:

        feet_patterns = [

            r"(?:height|ht)\s*[:=\-]?\s*"
            r"(\d+)\s*(?:ft|feet|foot)"
            r"\s*(\d+(?:\.\d+)?)?\s*"
            r"(?:in|inch|inches)?",

            r"(\d+)\s*(?:ft|feet|foot)"
            r"\s*(\d+(?:\.\d+)?)?\s*"
            r"(?:in|inch|inches)?"
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

                    if (
                        1 <= feet <= 8
                        and 0 <= inches < 12
                    ):

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

                except (ValueError, TypeError):

                    pass


    # ========================================================
    # HEIGHT - METERS
    # ========================================================

    if height is None:

        meter_patterns = [

            r"(?:height|ht)\s*[:=\-]?\s*"
            r"(\d+(?:\.\d+)?)\s*"
            r"(?:meters?|m)\b",

            r"(\d+\.\d+)\s*m\b"
        ]

        for pattern in meter_patterns:

            match = re.search(
                pattern,
                text_lower
            )

            if match:

                try:

                    meters = float(
                        match.group(1)
                    )

                    value = meters * 100

                    if 50 <= value <= 250:

                        height = round(
                            value,
                            1
                        )

                        break

                except (ValueError, TypeError):

                    pass


    return (
        sex,
        age,
        height,
        weight
    )


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
    ====================================================== */

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #666666;
        font-size: 18px;
        margin-bottom: 25px;
    }


    /* ======================================================
       RESULT BOX
    ====================================================== */

    .result-box {
        background-color: white;
        border: 1px solid #d9e1e8;
        border-radius: 18px;
        padding: 28px;
        margin-top: 15px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
    }

    .result-title {
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }

    .bmi-number {
        font-size: 60px;
        font-weight: 900;
        line-height: 1.1;
        margin: 5px 0 12px 0;
    }

    .category-badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 30px;
        background-color: #e8f5e9;
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 25px;
    }


    /* ======================================================
       RESULT DETAILS
    ====================================================== */

    .result-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        text-align: left;
    }

    .result-item {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px;
        display: flex;
        align-items: center;
        gap: 14px;
        min-height: 85px;
    }

    .result-icon {
        font-size: 28px;
        min-width: 35px;
    }

    .result-label {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 5px;
    }

    .result-value {
        font-size: 18px;
        font-weight: 800;
    }


    /* ======================================================
       AUTO FILL BOX
    ====================================================== */

    .auto-box {
        border: 1px solid #d9e1e8;
        border-radius: 12px;
        padding: 15px;
        margin-top: 12px;
        margin-bottom: 12px;
    }


    /* ======================================================
       FOOTER
    ====================================================== */

    .small-note {
        font-size: 13px;
        color: #666666;
        line-height: 1.6;
    }


    /* ======================================================
       MOBILE
    ====================================================== */

    @media (max-width: 700px) {

        .main-title {
            font-size: 34px;
        }

        .subtitle {
            font-size: 16px;
        }

        .result-box {
            padding: 20px;
        }

        .bmi-number {
            font-size: 48px;
        }

        .result-details {
            grid-template-columns: 1fr;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
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
# 1. PHOTO UPLOAD
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

    try:

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


        if st.button(
            "🔍 Extract Information",
            use_container_width=True
        ):

            with st.spinner(
                "🔍 Reading information from photo..."
            ):

                try:

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

                    if text.strip():

                        st.success(
                            "✅ Information extracted successfully!"
                        )

                    else:

                        st.warning(
                            "⚠️ No readable text was found."
                        )


                except Exception as e:

                    st.error(
                        f"❌ OCR processing error: {e}"
                    )

    except Exception as e:

        st.error(
            f"❌ Could not open the uploaded image: {e}"
        )


# ============================================================
# 2. EXTRACTED INFORMATION
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
                f"{st.session_state.ocr_height:.1f} cm"
            )

        else:

            st.warning(
                "⚠️ Height could not be detected."
            )


        if st.session_state.ocr_weight:

            st.success(
                f"⚖️ Weight: "
                f"{st.session_state.ocr_weight:.1f} kg"
            )

        else:

            st.warning(
                "⚠️ Weight could not be detected."
            )


    # ========================================================
    # AUTO FILL
    # ========================================================

    st.markdown(
        '<div class="auto-box">',
        unsafe_allow_html=True
    )

    st.write(
        "🤖 **Automatically fill the BMI form using "
        "the information extracted from the photo.**"
    )


    if st.button(
        "🤖 Auto Fill Form",
        type="primary",
        use_container_width=True
    ):

        filled = []


        if st.session_state.ocr_sex:

            st.session_state.sex = (
                st.session_state.ocr_sex
            )

            filled.append("Sex")


        if st.session_state.ocr_age:

            st.session_state.age = (
                st.session_state.ocr_age
            )

            filled.append("Age")


        if st.session_state.ocr_height:

            st.session_state.height_cm = (
                st.session_state.ocr_height
            )

            st.session_state.height_unit = (
                "Centimeters (cm)"
            )

            filled.append("Height")


        if st.session_state.ocr_weight:

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


    # ========================================================
    # RAW OCR
    # ========================================================

    with st.expander(
        "🔎 Show Raw Extracted Text"
    ):

        st.text(
            st.session_state.ocr_text
        )


# ============================================================
# 3. BMI FORM
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

        bmi = calculate_bmi(
            weight_kg,
            height_cm
        )

        category = get_category(
            bmi
        )

        calories = calculate_calories(
            sex,
            age,
            weight_kg,
            height_cm
        )

        (
            ideal_weight,
            healthy_min,
            healthy_max
        ) = calculate_healthy_weight_range(
            height_cm
        )


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
# 4. RESULTS
# ============================================================

if st.session_state.bmi_result is not None:

    bmi = st.session_state.bmi_result
    category = st.session_state.bmi_category
    calories = st.session_state.calories_result
    ideal_weight = st.session_state.ideal_weight
    healthy_min = st.session_state.healthy_weight_min
    healthy_max = st.session_state.healthy_weight_max


    st.subheader(
        "📊 4. Your Result"
    )


    # ========================================================
    # RESULT BOX
    # ========================================================

    result_html = f"""
    <div class="result-box">

        <div class="result-title">
            📊 BMI RESULT
        </div>

        <div class="bmi-number">
            {bmi:.1f}
        </div>

        <div class="category-badge">
            {category}
        </div>

        <div class="result-details">

            <div class="result-item">

                <div class="result-icon">
                    🎯
                </div>

                <div>
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

                <div>
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
    """


    # IMPORTANT:
    # unsafe_allow_html=True prevents the HTML
    # from appearing as text/code.

    st.markdown(
        result_html,
        unsafe_allow_html=True
    )


    # ========================================================
    # CALORIES
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

st.markdown(
    """
    | BMI | Category |
    |---|---|
    | Below 18.5 | Underweight |
    | 18.5 – 24.9 | Normal weight |
    | 25.0 – 29.9 | Overweight |
    | 30.0 or above | Obesity |
    """
)


# ============================================================
# RESET
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

    ⚠️ Educational calculator only.<br>
    OCR results should always be checked before use.<br>
    BMI and calorie values are estimates and are not
    a medical diagnosis.

    </div>
    """,
    unsafe_allow_html=True
)
