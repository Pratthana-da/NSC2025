import os
import requests
from supabase import create_client, Client
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "storybook")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def guess_mime_type(filename):
    if filename.endswith(".png"):
        return "image/png"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        return "image/jpeg"
    elif filename.endswith(".mp3"):
        return "audio/mpeg"
    elif filename.endswith(".wav"):
        return "audio/wav"
    else:
        return "application/octet-stream"


def upload_file_from_bytes(file_bytes: bytes, dest_path: str) -> str:
    """
    อัปโหลดไฟล์จาก bytes ไปยัง Supabase Storage
    """
    file_name = f"{uuid4().hex}_{os.path.basename(dest_path)}"
    final_path = f"{os.path.dirname(dest_path)}/{file_name}"

    mime_type = guess_mime_type(final_path)
    headers = {"content-type": str(mime_type)}  # ✅ แก้ปัญหา TypeError

    res = supabase.storage.from_(SUPABASE_BUCKET).upload(
        final_path,
        file_bytes,
        file_options=headers
    )

    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{final_path}"


def upload_file_from_url(file_url: str, dest_path: str) -> str:
    """
    ดาวน์โหลดไฟล์จาก URL แล้วอัปโหลดไปยัง Supabase Storage
    dest_path เช่น: "scenes/scene_1.png" หรือ "audios/scene_1.mp3"
    """
    response = requests.get(file_url)
    if response.status_code == 200:
        file_bytes = response.content
        return upload_file_from_bytes(file_bytes, dest_path)
    else:
        raise Exception(f"❌ Failed to download file from: {file_url}")
