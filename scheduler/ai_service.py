import io
from PIL import Image
import base64
import openai
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pathlib import Path
from .schemas import AIEditPayload, AIEditResponse, AICaptionPayload, AICaptionResponse
import os
import logging

logger = logging.getLogger(__name__)


openai_api_key = settings.OPENAI_API_KEY

def run_ai_tasks_for_schedule(schedule):
    """
    Orchestrates AI tasks based on the schedule's needs.
    Currently focuses on caption generation.
    """
    ai_generated_caption = None # Untuk menyimpan caption yang dihasilkan AI
    edited_media_url = None     # Untuk menyimpan URL media yang diedit AI
    
    # Prioritaskan AI Caption
    if schedule.needs_ai_caption:
        logger.info(f"Memulai tugas AI Caption untuk Jadwal ID: {schedule.id}")
        # Untuk captioning, kita biasanya menggunakan gambar asli
        first_asset = schedule.media_assets.first()
        if first_asset and first_asset.file:
            try:
                payload = AICaptionPayload(media_file_path=first_asset.file.path)
                response = ai_caption(payload)
                ai_generated_caption = response.caption
                logger.info(f"Caption AI berhasil dihasilkan untuk Jadwal ID: {schedule.id}")
            except Exception as e:
                logger.error(f"Gagal menjalankan AI Caption untuk Jadwal ID: {schedule.id}. Error: {e}")
                ai_generated_caption = "Error: Gagal menghasilkan caption."
    
    # Implementasikan logika untuk ai_edit jika diperlukan.
    if schedule.needs_ai_edit:
        logger.info(f"Memulai tugas AI Edit untuk Jadwal ID: {schedule.id}")
        first_asset = schedule.media_assets.first()
        if first_asset and first_asset.file and schedule.ai_edit_prompt:
            try:
                payload = AIEditPayload(
                    media_file_path=first_asset.file.path,
                    prompt=schedule.ai_edit_prompt
                )
                response = ai_edit(payload)
                edited_media_url = response.edited_media_file_path # Ini adalah URL ke file yang diedit
                logger.info(f"Gambar AI berhasil diedit untuk Jadwal ID: {schedule.id}. URL: {edited_media_url}")
            except Exception as e:
                logger.error(f"Gagal menjalankan AI Edit untuk Jadwal ID: {schedule.id}. Error: {e}")
                # Tangani error, mungkin set edited_media_url ke original atau None

    return {
        'ai_generated_caption': ai_generated_caption,
        'edited_media_url': edited_media_url
    }

def ai_edit(payload: AIEditPayload) -> AIEditResponse:
    """
    Runs AI editing tasks for a given image.
    
    """
    client = openai.OpenAI(api_key=openai_api_key)
    
    try: # request an Image Edit to openai
        logger.info(f"Proses: Melakukan permintaan AI Edit untuk {payload.media_file_path} ke OpenAI.")
        
        # Gambar harus dikonversi ke RGBA untuk DALL-E 2 edit
        img = Image.open(payload.media_file_path).convert("RGBA")
        
        # Simpan gambar RGBA ke stream byte di memori
        byte_stream = io.BytesIO()
        img.save(byte_stream, format="PNG")
        byte_stream.seek(0) # Kembali ke awal stream untuk dibaca

        # Berikan nama file dan data stream sebagai tuple untuk memastikan mimetype benar
        # Format: (nama_file, file_data, mimetype)
        image_data_tuple = ('image.png', byte_stream, 'image/png')

        result = client.images.edit(
            model="gpt-image-1", # Sesuai permintaan, model tidak diubah
            image=image_data_tuple, # Berikan tuple yang berisi data lengkap
            prompt=payload.prompt,
            n=1,
            quality='low'
        )
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        # Hasilkan nama file unik dan simpan menggunakan sistem penyimpanan Django
        original_path = Path(payload.media_file_path)
        edited_filename_stem = f"{original_path.stem}_edited_{os.urandom(4).hex()}"
        edited_filename = f"edited/{edited_filename_stem}{original_path.suffix}" # Simpan di subfolder 'edited'
        
        path_in_storage = default_storage.save(edited_filename, ContentFile(image_bytes))
        
        edited_url = default_storage.url(path_in_storage)
        logger.info(f"Berhasil menyimpan gambar hasil editan ke {edited_url}")
        return AIEditResponse(edited_media_file_path=edited_url) # Kembalikan URL lengkap
    except Exception as e:
        logger.error(f"Terjadi error saat melakukan permintaan AI Edit ke OpenAI. Error: {e}")
        raise e

def ai_caption(payload: AICaptionPayload) -> AICaptionResponse:
    """
    Runs AI captioning tasks for a given image.
    """
    client = openai.OpenAI(api_key=openai_api_key)
    
    try:
        logger.info(f"Proses: Melakukan permintaan AI Caption untuk {payload.media_file_path} ke OpenAI.")
        result = client.files.create(
                file=open(payload.media_file_path, "rb"),
                purpose="user_data",
                expires_after={
                    "anchor": "created_at",
                    "seconds" : 259200
                  }
                )
        file_id = result.id
    except Exception as e:
        logger.error(f"Terjadi error saat melakukan upload gambar ke OpenAI. Error: {e}")
        raise e
    try:
        response = client.responses.create(
            model="gpt-4.1",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Buatkan caption media sosial yang kreatif dan menarik untuk gambar ini. Maksimal 200 karakter."},
                    {
                        "type": "input_image",
                        "file_id": file_id,
                    },
                ],
            }],
        )
        logger.info(f"Berhasil melakukan caption generation.")
        caption = response.output_text
        return AICaptionResponse(caption=caption)
    except Exception as e:
        logger.error(f"Terjadi error saat melakukan permintaan Caption Generation ke OpenAI. Error: {e}")
        raise e