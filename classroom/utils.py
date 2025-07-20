from openai import OpenAI
from io import BytesIO
import PyPDF2
import json

client = OpenAI()

# ✅ 1. แปลงข้อความให้เป็นเสียง (TTS)
def generate_tts_audio(text, voice="nova"):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )
    return response.read()  # bytes ของไฟล์เสียง mp3


# ✅ 2. ดึงข้อความจาก PDF
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


# ✅ 3. สรุปเป็นนิทาน 20 ฉาก พร้อม prompt แบบ cartoon style
def summarize_to_scenes(raw_text):
    system_prompt = (
        "คุณคือผู้ช่วย AI ที่เชี่ยวชาญด้านการแปลงบทเรียนยาก ๆ ให้กลายเป็นนิทานภาพที่เด็กประถมเข้าใจได้ "
        "ภารกิจของคุณคือช่วยให้เด็กอายุ 7–12 ปีเข้าใจเนื้อหาทางวิชาการ เช่น วิทยาศาสตร์ คณิตศาสตร์ ภาษาไทย "
        "ผ่านเรื่องเล่าแบบนิทานที่มีตัวละคร ฉาก และภาพที่น่าสนใจ "
        "คุณต้องแปลงเนื้อหาให้เป็นเรื่องราว 20 ฉากต่อเนื่อง โดยใช้ภาษาง่าย สนุก และเชื่อมโยงกับชีวิตจริงของเด็ก "
        "ภาพประกอบจะใช้ prompt เพื่อสร้างภาพแนวการ์ตูน (cartoon style, storybook illustration) ซึ่งต้องสื่อฉากและตัวละครให้ชัดเจน"
    )

    user_prompt = f"""
บทเรียนต้นฉบับ:
\"\"\" 
{raw_text}
\"\"\"

🎯 จุดประสงค์ของการแปลง:
- ให้เด็กเข้าใจบทเรียนยาก ๆ ผ่านเรื่องราวที่สนุก
- ใช้ตัวละคร/ฉากที่เชื่อมโยงกับชีวิตประจำวัน
- เสริมทักษะการคิด เช่น การสังเกต คำนวณ คิดวิเคราะห์ ผ่านการเล่าเรื่อง
- ให้เด็กสนุกและไม่กลัวเนื้อหาทางวิชาการ

กรุณาสรุปบทเรียนนี้เป็น **นิทานสำหรับเด็ก 20 ฉาก** (scene 1-20) โดยมีรูปแบบ JSON ล้วน ๆ เท่านั้น
ห้ามมีคำอธิบายอื่นนอกจาก JSON

🔹 **แต่ละฉาก** ต้องประกอบด้วย:
- `"scene"`: เลขฉาก เช่น 1, 2, 3 ...
- `"text"`: เนื้อหานิทานในฉากนั้น ใช้ภาษาที่เข้าใจง่าย เหมาะกับเด็กประถม และเนื้อหาควรต่อเนื่องจากฉากก่อนหน้า
- `"image_prompt"`: prompt สำหรับสร้างภาพจาก DALL·E โดยต้องระบุ: ฉาก, ตัวละคร, สีสัน, อารมณ์ และ **สไตล์นิทานแนวการ์ตูน**
  (เช่น “เด็กชายกำลังถือสมุดภาพในห้องเรียนที่อบอุ่น มีครูใจดียืนข้างๆ แสงแดดส่องเข้าหน้าต่าง สไตล์การ์ตูน cartoon style, storybook illustration”)

📝 คำเตือนสำคัญ:
- ห้ามตอบ JSON ที่ไม่สมบูรณ์ เช่น ขาด ] หรือ " หรือ ปิดไม่ครบ
- หากฉากสุดท้ายไม่แน่ใจ ให้เว้นไว้หรือปิดด้วย []

ตัวอย่างรูปแบบ JSON:
[
  {{
    "scene": 1,
    "text": "น้องมายด์เดินเข้าไปในห้องเรียนใหม่ ที่เต็มไปด้วยหนังสือเกี่ยวกับพลังงานแสงอาทิตย์...",
    "image_prompt": "เด็กหญิงผมยาวใส่ชุดนักเรียน ยืนในห้องเรียนสว่างไสว มีแผงโซลาร์เซลล์บนผนัง สไตล์การ์ตูน cartoon style, storybook illustration"
  }},
  ...
]
"""

    from openai import OpenAI
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    result_text = response.choices[0].message.content.strip()

    # ✅ ล้าง ```json หรือ ```
    if result_text.startswith("```json"):
        result_text = result_text[7:]
    elif result_text.startswith("```"):
        result_text = result_text[3:]
    if result_text.endswith("```"):
        result_text = result_text[:-3]

    # ✅ พิมพ์ส่วนท้ายไว้ debug
    print("===== JSON TAIL (last 1000 chars) =====")
    print(result_text)
    print("========================================")

    try:
        return json.loads(result_text)

    except json.JSONDecodeError as e:
        print("❌ JSONDecodeError:", str(e))

        # ✅ แก้เบื้องต้น: ตัดฉากสุดท้ายที่ไม่สมบูรณ์ออก
        if result_text.endswith("]") is False:
            # ตัดองค์ประกอบที่เปิดอยู่ไม่ครบ เช่น scene 19
            fixed = result_text.rsplit('{', 1)[0].rstrip(', \n') + "\n]"
            try:
                return json.loads(fixed)
            except Exception as e2:
                raise ValueError("❌ แก้แล้วแต่ยังพังอยู่: " + str(e2))
        else:
            raise ValueError("❌ ไม่สามารถแปลงผลลัพธ์จาก GPT เป็น JSON ได้: " + str(e))


# ✅ 4. สร้างภาพจาก DALL·E พร้อมเพิ่ม cartoon style อัตโนมัติ
def generate_dalle_image(prompt):
    styled_prompt = prompt + ", cartoon style, storybook illustration, soft lighting, colorful"
    response = client.images.generate(
        model="dall-e-3",
        prompt=styled_prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return response.data[0].url
