from openai import OpenAI
from io import BytesIO
import PyPDF2
import json

client = OpenAI()

def generate_tts_audio(text, voice="nova"):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )
    return response.read()  # bytes

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def summarize_to_scenes(raw_text):
    system_prompt = (
        "คุณคือผู้ช่วยที่แปลงบทเรียนให้เป็นนิทานเด็กแบบง่าย "
        "โดยแบ่งออกเป็น 20 ฉาก พร้อมคำอธิบายและ prompt สำหรับสร้างภาพแนวนิทาน"
    )

    user_prompt = f"""
บทเรียน:
{raw_text}

กรุณาสรุปเนื้อหาเป็น JSON ล้วน ๆ เท่านั้น ห้ามมีคำอธิบายอื่นนอกจาก JSON ตัวอย่าง:
[
  {{
    "scene": 1,
    "text": "เนื้อหาในฉากที่ 1 แบบเข้าใจง่ายสำหรับเด็ก",
    "image_prompt": "prompt สำหรับสร้างภาพแนวนิทาน"
  }},
  ...
]
"""

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    result_text = response.choices[0].message.content.strip()

    # ✅ ล้าง markdown wrapper เช่น ```json ... ``` หรือ ```
    if result_text.startswith("```json"):
        result_text = result_text[7:]
    elif result_text.startswith("```"):
        result_text = result_text[3:]
    if result_text.endswith("```"):
        result_text = result_text[:-3]

    # ✅ Debug ช่วยเช็กว่า GPT ตอบอะไร
    print("===== GPT RESPONSE CLEANED =====")
    print(result_text)
    print("===== END CLEANED =====")

    try:
        return json.loads(result_text)
    except Exception as e:
        raise ValueError("ไม่สามารถแปลงผลลัพธ์จาก GPT เป็น JSON ได้: " + str(e))


def generate_dalle_image(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return response.data[0].url
