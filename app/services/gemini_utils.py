import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# --- الإعدادات الأولية ---
# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# إعداد نظام التسجيل
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- إعداد Gemini API ---
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("لم يتم العثور على متغير البيئة GEMINI_API_KEY.")
    
    genai.configure(api_key=GEMINI_API_KEY)

    # --- إعدادات النموذج ---
    # ✅ الإصلاح: استخدام نموذج أحدث وأكثر كفاءة مثل 'gemini-1.5-flash'
    # وتحديد إعدادات الأمان والتوليد
    generation_config = {
      "temperature": 0.7,
      "top_p": 1,
      "top_k": 1,
      "max_output_tokens": 2048,
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
except (ValueError, Exception) as e:
    logging.critical(f"فشل فادح في إعداد Gemini API: {e}")
    model = None

def generate_gemini_summary(text_to_summarize: str) -> str:
    """
    توليد ملخص لنص معين باستخدام Gemini API مع معالجة دقيقة للأخطاء.
    """
    if not model:
        logging.error("نموذج Gemini غير متاح. لا يمكن إنشاء ملخص.")
        return "ERROR: Gemini model not configured."

    # ✅ التحسين: استخدام prompt أكثر تحديداً وفعالية للتلخيص باللغة العربية
    prompt = f"""
    لخص النص التالي في فقرة واحدة موجزة وواضحة باللغة العربية. 
    يجب أن يركز الملخص على الأفكار الرئيسية فقط ويتجنب التفاصيل غير الضرورية.

    النص الأصلي:
    ---
    {text_to_summarize}
    ---

    الملخص:
    """
    
    try:
        logging.info("Sending request to Gemini API for summarization...")
        response = model.generate_content(prompt)
        
        # التحقق من وجود محتوى في الرد
        if response.parts:
            summary = response.text
            logging.info("Successfully received summary from Gemini API.")
            return summary
        else:
            # معالجة حالة الرد الفارغ أو المحظور
            logging.warning("Gemini API returned an empty or blocked response.")
            return "ERROR: Failed to generate summary (empty or blocked response)."
            
    except Exception as e:
        logging.error(f"An error occurred while calling the Gemini API: {e}")
        return f"ERROR: An exception occurred during the API call: {e}"


