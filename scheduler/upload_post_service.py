from .models import Schedule
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def schedule_post_upload(schedule: Schedule):
    """
    Schedules a post upload by calling an external API.
    It handles single image, carousel, and video posts.
    """
    logger.info(f"Memulai permintaan Upload Post dengan API untuk Schedule ID: {schedule.id}")
    try:
        BASE_URL = "https://api.upload-post.com/api/"
        headers = {
            "Authorization": f"api_key {settings.UPLOAD_POST_API_KEY}"
        }
        # The API seems to expect 'platform[]' for multiple values
        platforms = schedule.platform
        if platforms == 'BOTH':
            platforms = ['IG', 'TIKTOK']
        else:
            platforms = [platforms]

        data_payload = {
            "user": 'karenbot',
            "platform[]": platforms,
            "title": schedule.ai_generated_caption or schedule.caption, # Use AI caption if available
            "scheduled_date": schedule.schedule_time.isoformat()
        }

        files_payload = []
        url = ""

        if schedule.media_type == 'SINGLE_IMAGE':
            logger.info("Memproses unggahan Jadwal Gambar Tunggal")
            url = f"{BASE_URL}/upload_photos"
            asset = schedule.media_assets.first()
            if asset and asset.file:
                with asset.file.open('rb') as f:
                    files_payload.append(('photos', (asset.file.name, f.read(), 'image/jpeg')))

        elif schedule.media_type == 'CAROUSEL':
            logger.info("Memproses unggahan Jadwal Carousel")
            url = f"{BASE_URL}/upload_photos" # Asumsi endpoint yang sama
            assets = schedule.media_assets.all()
            for asset in assets:
                if asset.file:
                    with asset.file.open('rb') as f:
                        files_payload.append(('photos', (asset.file.name, f.read(), 'image/jpeg')))

        elif schedule.media_type == 'VIDEO':
            logger.info("Memproses unggahan Jadwal Video")
            url = f"{BASE_URL}/upload"
            asset = schedule.media_assets.first()
            if asset and asset.file:
                with asset.file.open('rb') as f:
                    files_payload.append(('video', (asset.file.name, f.read(), 'video/mp4')))

        if not url or not files_payload:
            logger.error(f"Tidak dapat memproses jadwal {schedule.id}: URL endpoint atau file tidak valid.")
            return None

        response = requests.post(
            url,
            headers=headers,
            data=data_payload,
            files=files_payload
        )

        if response.status_code in [200, 202]:
            logger.info(f"Berhasil mengirim permintaan ke Upload Post API untuk Jadwal {schedule.id}. Status: {response.status_code}")
            # Save the job ID from the API response
            response_data = response.json()
            schedule.upload_job_id = response_data.get('job_id') # Assuming the key is 'job_id'
            schedule.save()
            return response_data
        else:
            logger.error(f"Gagal mengirim permintaan ke Upload Post API untuk Jadwal {schedule.id}. Status: {response.status_code}, Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Terjadi error saat melakukan permintaan ke Upload Post API untuk Jadwal {schedule.id}. Error: {e}")
        # It's better not to raise the exception up to the view unless the view can handle it.
        # Returning None is often safer.
        return None
