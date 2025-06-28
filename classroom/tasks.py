# from celery import shared_task
# from .models import Storybook, Scene
# from .supabase_utils import upload_file_from_url
# from .utils import extract_text_from_pdf, summarize_to_scenes, generate_dalle_image
# from django.db import transaction

# @shared_task
# def process_storybook_async(storybook_id):
#     try:
#         storybook = Storybook.objects.get(id=storybook_id)
#         lesson_path = storybook.file.path

#         # 1. สกัดข้อความจากไฟล์ PDF
#         raw_text = extract_text_from_pdf(lesson_path)

#         # 2. แบ่งเป็นฉากด้วย GPT
#         scenes_data = summarize_to_scenes(raw_text)

#         with transaction.atomic():
#             for scene_dict in scenes_data:
#                 text = scene_dict["text"]
#                 prompt = scene_dict["image_prompt"]
#                 scene_number = scene_dict["scene"]

#                 # 3. สร้างภาพจาก DALL·E
#                 dalle_url = generate_dalle_image(prompt)

#                 # 4. อัปโหลดเข้า Supabase Storage (โหลดจาก URL แล้ว re-upload)
#                 supabase_image_url = upload_file_from_url(dalle_url, f"scenes/storybook_{storybook.id}_scene_{scene_number}.png")

#                 # 5. สร้าง Scene record
#                 Scene.objects.create(
#                     storybook=storybook,
#                     scene_number=scene_number,
#                     text=text,
#                     image_prompt=prompt,
#                     image_url=supabase_image_url,
#                 )

#             # 6. Mark as ready
#             storybook.is_ready = True
#             storybook.save()

#     except Exception as e:
#         storybook = Storybook.objects.filter(id=storybook_id).first()
#         if storybook:
#             storybook.is_failed = True
#             storybook.save()
#         raise e  # Optional: log หรือแจ้งผ่าน email

# tasks.py
from celery import shared_task
from .models import Storybook, Scene
from .supabase_utils import upload_file_from_url, upload_file_from_bytes
from .utils import extract_text_from_pdf, summarize_to_scenes, generate_dalle_image, generate_tts_audio
from django.db import transaction

@shared_task
def process_storybook_async(storybook_id):
    try:
        storybook = Storybook.objects.get(id=storybook_id)
        lesson_path = storybook.file.path

        # 1. ดึงข้อความจาก PDF
        raw_text = extract_text_from_pdf(lesson_path)

        # 2. สรุปเนื้อหา → แบ่งเป็นฉาก (GPT)
        scenes_data = summarize_to_scenes(raw_text)
        

        with transaction.atomic():
            for scene_dict in scenes_data:
                scene_number = scene_dict["scene"]
                text = scene_dict["text"]
                prompt = scene_dict["image_prompt"]

                # 3. สร้างภาพจาก DALL·E
                dalle_url = generate_dalle_image(prompt)
                supabase_image_url = upload_file_from_url(
                    dalle_url,
                    f"scenes/storybook_{storybook.id}_scene_{scene_number}.png"
                )

                # 4. สร้างเสียงจาก GPT TTS
                audio_bytes = generate_tts_audio(text)
                supabase_audio_url = upload_file_from_bytes(
                    audio_bytes,
                    f"audios/storybook_{storybook.id}_scene_{scene_number}.mp3"
                )

                # 5. บันทึกฉากลงฐานข้อมูล
                Scene.objects.create(
                    storybook=storybook,
                    scene_number=scene_number,
                    text=text,
                    image_prompt=prompt,
                    image_url=supabase_image_url,
                    audio_url=supabase_audio_url
                )

            # 6. อัปเดตสถานะ
            storybook.is_ready = True
            storybook.save()

    except Exception as e:
        storybook = Storybook.objects.filter(id=storybook_id).first()
        if storybook:
            storybook.is_failed = True
            storybook.save()
        raise e
