 #```python
import streamlit as st
import re
import io
import os
import math
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BMI Calculator",
    page_icon="⚖️",
    layout="centered"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

h1 {
    text-align: center;
}

.subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 25px;
}


/* =========================
   BMI RESULT BOX
   ========================= */

.result-box {
    background: white;
    border-radius: 18px;
    padding: 25px;
    margin-top: 20px;
    margin-bottom: 20px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    text-align: center;
}

.result-title {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 10px;
}

.bmi-number {
    font-size: 55px;
    font-weight: 800;
    margin: 5px 0;
}

.category-badge {
    display: inline-block;
    padding: 8px 20px;
    border-radius: 25px;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 25px;
    background: #fff3cd;
    color: #856404;
}

.result-details {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-top: 15px;
}

.result-item {
    display: flex;
    align-items: center;
    text-align: left;
    padding: 15px;
    border-radius: 12px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
}

.result-icon {
    font-size: 28px;
    margin-right: 12px;
}

.result-label {
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 4px;
}

.result-value {
    font-size: 17px;
    font-weight: 700;
}


/* =========================
   INFO BOX
   ========================= */

.info-box {
    padding: 15px;
    border-radius: 12px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    margin-top: 15px;
}


/* =========================
   MOBILE
   ========================= */

@media (max-width: 700px) {

    .result-details {
        grid-template-columns: 1fr;
    }

    .bmi-number {
        font-size: 45px;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DEFAULT VALUES
# ============================================================

DEFAULTS = {
    "sex": "Male",
    "age": 25,
    "height_unit": "Centimeters (cm)",
    "weight_unit": "Kilograms (kg)",
    "height_cm": 170.0,
    "height_feet": 5,
    "height_inches": 7.0,
    "weight_kg": 70.0,
    "weight_lb": 154.3,

    "extracted_sex": None,
    "extracted_age": None,
    "extracted_height_cm": None,
    "extracted_weight_kg": None,
    "ocr_text": "",
    "bmi_result": None,

    "uploader_key": 0
}


# ============================================================
# INITIALIZE SESSION STATE
# ============================================================

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# RESET FUNCTION
# ============================================================

def reset_application():

    for key, value in DEFAULTS.items():

        if isinstance(value, list):
            st.session_state[key] = value.copy()

        elif isinstance(value, dict):
            st.session_state[key] = value.copy()

        else:
            st.session_state[key] = value

    # Change uploader key so the uploaded image disappears
    st.session_state.uploader_key += 1


# ============================================================
# CONVERSION FUNCTIONS
# ============================================================

def pounds_to_kg(lb):
    return lb * 0.45359237


def kg_to_pounds(kg):
    return kg / 0.45359237


def feet_inches_to_cm(feet, inches):
    return (feet * 12 + inches) * 2.54


# ============================================================
# BMI CALCULATION
# ============================================================

def calculate_bmi(weight_kg, height_cm):

    if weight_kg <= 0 or height_cm <= 0:
        return None

    height_m = height_cm / 100

    return weight_kg / (height_m ** 2)


# ============================================================
# BMI CATEGORY
# ============================================================

def get_bmi_category(bmi):

    if bmi < 18.5:
        return "Underweight"

    elif bmi < 25:
        return "Normal weight"

    elif bmi < 30:
        return "Overweight"

    else:
        return "Obesity"


# ============================================================
# HEALTHY WEIGHT RANGE
# ============================================================

def healthy_weight_range(height_cm):

    height_m = height_cm / 100

    minimum = 18.5 * (height_m ** 2)
    maximum = 24.9 * (height_m ** 2)

    return minimum, maximum


# ============================================================
# IDEAL WEIGHT
# ============================================================

def calculate_ideal_weight(height_cm):

    height_m = height_cm / 100

    # Reference BMI = 21.7
    return 21.7 * (height_m ** 2)


# ============================================================
# CALORIES
# ============================================================

def calculate_daily_calories(sex, age, weight_kg, height_cm):

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

    # Sedentary activity factor
    return bmr * 1.2


# ============================================================
# OCR IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image):

    image = image.convert("RGB")

    # Upscale small images
    width, height = image.size

    if width < 1800:

        scale = 1800 / width

        image = image.resize(
            (
                int(width * scale),
                int(height * scale)
            )
        )

    # Grayscale
    image = image.convert("L")

    # Increase contrast
    image = ImageEnhance.Contrast(image).enhance(3.0)

    # Increase sharpness
    image = ImageEnhance.Sharpness(image).enhance(2.5)

    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)

    return image


# ============================================================
# OCR TEXT EXTRACTION
# ============================================================

def extract_text_from_image(image):

    processed = preprocess_image(image)

    text = pytesseract.image_to_string(
        processed,
        config="--psm 6"
    )

    return text


# ============================================================
# EXTRACT SEX
# ============================================================

def extract_sex(text):

    text_lower = text.lower()

    male_patterns = [
        r"\bmale\b",
        r"\bman\b",
        r"\bgender\s*[:\-]?\s*m\b",
        r"\bsex\s*[:\-]?\s*m\b"
    ]

    female_patterns = [
        r"\bfemale\b",
        r"\bwoman\b",
        r"\bgender\s*[:\-]?\s*f\b",
        r"\bsex\s*[:\-]?\s*f\b"
    ]

    for pattern in male_patterns:

        if re.search(pattern, text_lower):
            return "Male"

    for pattern in female_patterns:

        if re.search(pattern, text_lower):
            return "Female"

    return None


# ============================================================
# EXTRACT AGE
# ============================================================

def extract_age(text):

    patterns = [

        r"(?:age|aged)\s*[:\-]?\s*(\d{1,3})\s*(?:years?|yrs?)?",

        r"(\d{1,3})\s*(?:years?|yrs?)\s*(?:old)?"

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for value in matches:

            age = int(value)

            if 1 <= age <= 120:
                return age

    return None


# ============================================================
# EXTRACT HEIGHT
# ============================================================

def extract_height(text):

    # --------------------------------------------------------
    # Feet + inches
    # Example: Height: 5 ft 7 in
    # --------------------------------------------------------

    patterns_feet = [

        r"(\d{1,2})\s*(?:ft|feet|foot)\s*"
        r"(\d{1,2}(?:\.\d+)?)\s*(?:in|inch|inches)",

        r"(\d{1,2})\s*['′]\s*"
        r"(\d{1,2}(?:\.\d+)?)\s*[\"″]"

    ]

    for pattern in patterns_feet:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            feet = float(match.group(1))
            inches = float(match.group(2))

            return feet_inches_to_cm(feet, inches)


    # --------------------------------------------------------
    # Centimeters
    # --------------------------------------------------------

    patterns_cm = [

        r"(?:height|ht)\s*[:\-]?\s*"
        r"(\d{2,3}(?:\.\d+)?)\s*(?:cm|centimeters?)",

        r"(\d{2,3}(?:\.\d+)?)\s*(?:cm|centimeters?)"

    ]

    for pattern in patterns_cm:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            height = float(match.group(1))

            if 50 <= height <= 250:
                return height


    # --------------------------------------------------------
    # Meters
    # Example: 1.70 m
    # --------------------------------------------------------

    patterns_m = [

        r"(?:height|ht)\s*[:\-]?\s*"
        r"(\d(?:\.\d+)?)\s*(?:m|meter|meters)\b",

        r"\b(1\.\d{1,2})\s*m\b"

    ]

    for pattern in patterns_m:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            height = float(match.group(1)) * 100

            if 50 <= height <= 250:
                return height


    return None


# ============================================================
# EXTRACT WEIGHT
# ============================================================

def extract_weight(text):

    # --------------------------------------------------------
    # Kilograms
    # --------------------------------------------------------

    patterns_kg = [

        r"(?:weight|wt)\s*[:\-]?\s*"
        r"(\d{2,3}(?:\.\d+)?)\s*(?:kg|kgs|kilograms?)",

        r"(\d{2,3}(?:\.\d+)?)\s*(?:kg|kgs|kilograms?)"

    ]

    for pattern in patterns_kg:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            weight = float(match.group(1))

            if 10 <= weight <= 400:
                return weight


    # --------------------------------------------------------
    # Pounds
    # --------------------------------------------------------

    patterns_lb = [

        r"(?:weight|wt)\s*[:\-]?\s*"
        r"(\d{2,3}(?:\.\d+)?)\s*(?:lb|lbs|pounds?)",

        r"(\d{2,3}(?:\.\d+)?)\s*(?:lb|lbs|pounds?)"

    ]

    for pattern in patterns_lb:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            pounds = float(match.group(1))

            if 20 <= pounds <= 880:
                return pounds_to_kg(pounds)


    return None


# ============================================================
# DISPLAY BMI RESULT
# ============================================================

def display_bmi_result(
    bmi,
    category,
    ideal_weight,
    healthy_min,
    healthy_max
):

    # --------------------------------------------------------
    # Category style
    # --------------------------------------------------------

    if category == "Underweight":

        badge_background = "#cfe2ff"
        badge_color = "#084298"

    elif category == "Normal weight":

        badge_background = "#d1e7dd"
        badge_color = "#0f5132"

    elif category == "Overweight":

        badge_background = "#fff3cd"
        badge_color = "#856404"

    else:

        badge_background = "#f8d7da"
        badge_color = "#842029"


    # --------------------------------------------------------
    # Result HTML
    # --------------------------------------------------------

    result_html = f"""
    <div class="result-box">

        <div class="result-title">
            📊 BMI RESULT
        </div>

        <div class="bmi-number">
            {bmi:.1f}
        </div>

        <div class="category-badge"
             style="
             background:{badge_background};
             color:{badge_color};
             ">
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
    # unsafe_allow_html=True makes Streamlit render
    # the HTML instead of showing the HTML code.

    st.markdown(
        result_html,
        unsafe_allow_html=True
    )


# ============================================================
# TITLE
# ============================================================

st.title("⚖️ BMI Calculator")

st.markdown(
    '<div class="subtitle">'
    'Calculate your Body Mass Index and healthy weight range'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# RESET BUTTON
# ============================================================

if st.button(
    "🔄 Reset",
    use_container_width=True
):

    reset_application()

    st.rerun()


# ============================================================
# MANUAL BMI CALCULATOR
# ============================================================

st.header("🧮 Manual BMI Calculator")


# ------------------------------------------------------------
# Personal Information
# ------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    sex = st.selectbox(
        "Sex",
        ["Male", "Female"],
        key="sex"
    )

with col2:

    age = st.number_input(
        "Age",
        min_value=1,
        max_value=120,
        step=1,
        key="age"
    )


# ============================================================
# HEIGHT
# ============================================================

height_unit = st.selectbox(
    "Height Unit",
    [
        "Centimeters (cm)",
        "Feet & Inches"
    ],
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

        feet = st.number_input(
            "Feet",
            min_value=1,
            max_value=8,
            step=1,
            key="height_feet"
        )

    with col2:

        inches = st.number_input(
            "Inches",
            min_value=0.0,
            max_value=11.0,
            step=0.1,
            key="height_inches"
        )

    height_cm = feet_inches_to_cm(
        feet,
        inches
    )


# ============================================================
# WEIGHT
# ============================================================

weight_unit = st.selectbox(
    "Weight Unit",
    [
        "Kilograms (kg)",
        "Pounds (lb)"
    ],
    key="weight_unit"
)


if weight_unit == "Kilograms (kg)":

    weight_kg = st.number_input(
        "Weight (kg)",
        min_value=10.0,
        max_value=400.0,
        step=0.1,
        key="weight_kg"
    )

else:

    weight_lb = st.number_input(
        "Weight (lb)",
        min_value=20.0,
        max_value=880.0,
        step=0.1,
        key="weight_lb"
    )

    weight_kg = pounds_to_kg(weight_lb)


# ============================================================
# CALCULATE BUTTON
# ============================================================

if st.button(
    "📊 Calculate BMI",
    type="primary",
    use_container_width=True
):

    # Validation

    if age <= 0:

        st.error("Please enter a valid age.")

    elif height_cm <= 0:

        st.error("Please enter a valid height.")

    elif weight_kg <= 0:

        st.error("Please enter a valid weight.")

    else:

        bmi = calculate_bmi(
            weight_kg,
            height_cm
        )

        category = get_bmi_category(bmi)

        healthy_min, healthy_max = healthy_weight_range(
            height_cm
        )

        ideal_weight = calculate_ideal_weight(
            height_cm
        )

        calories = calculate_daily_calories(
            sex,
            age,
            weight_kg,
            height_cm
        )

        # Save result
        st.session_state.bmi_result = {
            "bmi": bmi,
            "category": category,
            "ideal_weight": ideal_weight,
            "healthy_min": healthy_min,
            "healthy_max": healthy_max,
            "calories": calories
        }


# ============================================================
# DISPLAY SAVED RESULT
# ============================================================

if st.session_state.bmi_result is not None:

    result = st.session_state.bmi_result

    display_bmi_result(
        result["bmi"],
        result["category"],
        result["ideal_weight"],
        result["healthy_min"],
        result["healthy_max"]
    )

    st.info(
        f"🔥 Estimated daily calories: "
        f"**{result['calories']:.0f} kcal/day** "
        f"(sedentary activity level)"
    )


# ============================================================
# PHOTO OCR SECTION
# ============================================================

st.divider()

st.header("📷 Extract Information from Photo")

st.write(
    "Upload a photo containing weight, height, age, or sex. "
    "The application will try to extract the information automatically."
)


uploaded_file = st.file_uploader(
    "Upload Photo",
    type=["jpg", "jpeg", "png"],
    key=f"photo_uploader_{st.session_state.uploader_key}"
)


# ============================================================
# OCR PROCESSING
# ============================================================

if uploaded_file is not None:

    try:

        image_bytes = uploaded_file.read()

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        st.image(
            image,
            caption="Uploaded Photo",
            use_container_width=True
        )


        # ----------------------------------------------------
        # Extract text
        # ----------------------------------------------------

        with st.spinner(
            "🔍 Reading information from the photo..."
        ):

            ocr_text = extract_text_from_image(
                image
            )


        st.session_state.ocr_text = ocr_text


        # ----------------------------------------------------
        # Extract values
        # ----------------------------------------------------

        extracted_sex = extract_sex(
            ocr_text
        )

        extracted_age = extract_age(
            ocr_text
        )

        extracted_height_cm = extract_height(
            ocr_text
        )

        extracted_weight_kg = extract_weight(
            ocr_text
        )


        # Save extracted information

        st.session_state.extracted_sex = extracted_sex

        st.session_state.extracted_age = extracted_age

        st.session_state.extracted_height_cm = (
            extracted_height_cm
        )

        st.session_state.extracted_weight_kg = (
            extracted_weight_kg
        )


        # ====================================================
        # EXTRACTION RESULTS
        # ====================================================

        st.subheader("🔎 Extracted Information")


        col1, col2 = st.columns(2)


        with col1:

            if extracted_sex:

                st.success(
                    f"👤 Sex: **{extracted_sex}**"
                )

            else:

                st.warning(
                    "⚠️ Sex could not be detected."
                )


            if extracted_age:

                st.success(
                    f"🎂 Age: **{extracted_age} years**"
                )

            else:

                st.warning(
                    "⚠️ Age could not be detected."
                )


        with col2:

            if extracted_height_cm:

                st.success(
                    f"📏 Height: "
                    f"**{extracted_height_cm:.1f} cm**"
                )

            else:

                st.warning(
                    "⚠️ Height could not be detected."
                )


            if extracted_weight_kg:

                st.success(
                    f"⚖️ Weight: "
                    f"**{extracted_weight_kg:.1f} kg**"
                )

            else:

                st.warning(
                    "⚠️ Weight could not be detected."
                )


        # ====================================================
        # AUTO FILL FORM
        # ====================================================

        st.markdown("###")

        if st.button(
            "✨ Auto Fill Form",
            use_container_width=True
        ):

            # -----------------------------------------------
            # Sex
            # -----------------------------------------------

            if extracted_sex in [
                "Male",
                "Female"
            ]:

                st.session_state.sex = extracted_sex


            # -----------------------------------------------
            # Age
            # -----------------------------------------------

            if extracted_age is not None:

                st.session_state.age = extracted_age


            # -----------------------------------------------
            # Height
            # -----------------------------------------------

            if extracted_height_cm is not None:

                st.session_state.height_unit = (
                    "Centimeters (cm)"
                )

                st.session_state.height_cm = (
                    round(
                        extracted_height_cm,
                        1
                    )
                )


            # -----------------------------------------------
            # Weight
            # -----------------------------------------------

            if extracted_weight_kg is not None:

                st.session_state.weight_unit = (
                    "Kilograms (kg)"
                )

                st.session_state.weight_kg = (
                    round(
                        extracted_weight_kg,
                        1
                    )
                )


            st.success(
                "✅ Information automatically filled into the form."
            )

            st.rerun()


        # ====================================================
        # RAW OCR TEXT
        # ====================================================

        with st.expander(
            "📄 View Extracted Text"
        ):

            if ocr_text.strip():

                st.text(
                    ocr_text
                )

            else:

                st.warning(
                    "No text was detected in the image."
                )


    except Exception as e:

        st.error(
            f"❌ Could not process the image: {e}"
        )


# ============================================================
# BMI REFERENCE
# ============================================================

st.divider()

st.header("📚 BMI Reference")

st.markdown("""
| BMI | Category |
|---|---|
| Below 18.5 | Underweight |
| 18.5 – 24.9 | Normal weight |
| 25.0 – 29.9 | Overweight |
| 30.0 or above | Obesity |
""")


st.caption(
    "BMI is a screening measure and should not be used as a "
    "diagnosis. For health decisions, consult a qualified "
    "health professional."
)

