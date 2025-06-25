# classroom/tasks.py
import os
from celery import shared_task
from .models import Storybook, Scene
from .utils import summarize_to_scenes, generate_dalle_image, extract_text_from_pdf

@shared_task
def process_storybook_async(storybook_id):
    storybook = Storybook.objects.get(id=storybook_id)
    try:
        # 1. ดึงข้อความจากไฟล์ PDF
        text = extract_text_from_pdf(storybook.file.path)

        # 2. ใช้ GPT สรุปเป็นฉาก
        scenes_data = summarize_to_scenes(text)

        # 3. วนสร้างภาพและบันทึกแต่ละฉาก
        for item in scenes_data:
            print(f"🖼️ สร้างภาพสำหรับฉาก {item['scene']}...")
            image_url = generate_dalle_image(item['image_prompt'])

            Scene.objects.create(
                storybook=storybook,
                scene_number=item['scene'],
                text=item['text'],
                image_prompt=item['image_prompt'],
                image_url=image_url,
            )

        # 4. อัปเดตสถานะ
        storybook.is_ready = True
        storybook.save()

    except Exception as e:
        storybook.is_failed = True
        storybook.save()
        print("❌ ERROR:", e)
        raise e
