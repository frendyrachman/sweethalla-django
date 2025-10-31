import logging
import requests
from django.conf import settings
from datetime import timedelta
from .schemas import edit_schedule_payload, edit_schedule_response



logger = logging.getLogger(__name__)

def schedule_post_upload(schedule):
    """
    Schedules a post upload by calling an external API.
    It handles single image, carousel, and video posts.
    """
    logger.info(f"Memulai permintaan Upload Post dengan API untuk Schedule ID: {schedule.id}")
    try:
        BASE_URL = "https://api.upload-post.com/api" # Hapus garis miring di akhir
        headers = {
            "Authorization": f"api_key {settings.UPLOAD_POST_API_KEY}"
        }
        # The API seems to expect 'platform[]' for multiple values
        platforms = schedule.platform
        if platforms == 'BOTH':
            platforms = ['IG', 'TIKTOK']
        else:
            platforms = [platforms]

        # Perhitungan sederhana: Kurangi 7 jam dari waktu jadwal untuk mendapatkan UTC
        # Asumsi waktu input adalah GMT+7
        utc_scheduled_date = schedule.schedule_time - timedelta(hours=7)

        data_payload = {
            "user": 'karenbot',
            "platform[]": platforms,
            "title": schedule.caption, # Gunakan caption final yang sudah dikonfirmasi
            "scheduled_date": utc_scheduled_date.isoformat(), # Kirim waktu yang sudah dikonversi ke UTC
            "media_type": schedule.content_type
        }

        files_payload = []
        url = ""

        if schedule.media_type == 'IMAGE':
            logger.info("Memproses unggahan Jadwal Gambar")
            url = f"{BASE_URL}/upload_photos"
            assets = schedule.media_assets.all()
            for asset in assets:
                # Gunakan file yang sudah diedit jika ada, jika tidak, gunakan file asli
                file_to_upload = asset.edited_file if asset.edited_file else asset.file
                if file_to_upload:
                    with file_to_upload.open('rb') as f:
                        # Gunakan nama file asli untuk API
                        files_payload.append(('photos[]', (asset.file.name, f.read(), 'image/jpeg')))

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

def get_schedule():
    """
    Mengambil jadwal upload yang sudah terkirim ke Upload Post
    """
    logger.info("Mengambil Seluruh jadwal di Upload Post")
    try:
        url = "https://api.upload-post.com/api/uploadposts/schedule"
        headers = {
            "Authorization": f"Apikey {settings.UPLOAD_POST_API_KEY}"
        }
        response = requests.get(url=url, headers=headers)
        schedule_list = []
        if response.status_code == 200:
            logger.info(f"Berhasil mengambil daftar jadwal")
            schedule_list.append(response.json())
            return schedule_list
        else:
            logger.error(f"Terjadi error saat mengambil data jadwal di Upload Post. Error Code: {response.status_code}. Error Message: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": "Gagal terhubung ke UploadPost API.",
            "detail": str(e)
        }

def delete_upload_schedule(job_id):
    """
    Mengirimkan permintaan hapus atau cancel jadwal ke UploadPost
    """
    logger.info(f"Mengirim permintaan cancel upload schedule.")
    try:
        BASE_URL = "https://api.upload-post.com/api/schedule/" # Hapus garis miring di akhir
        headers = {
            "Authorization": f"api_key {settings.UPLOAD_POST_API_KEY}"
        }
        response = requests.delete(f"{BASE_URL}{job_id}", headers=headers)
        if response.status_code in [200, 202]:
            logger.info(f"Berhasil mengirim permintaan cancel ke Upload Post API untuk Jadwal {job_id}.")
            return response.json()
        else:
            logger.error(f"Error Response from upload post API. Error: {response.json}")
            return 
    except Exception as e:
        logger.error("Error Requesting delete schedule.")
        
def edit_schedule(payload: edit_schedule_payload) -> edit_schedule_response:
    """
    Mengirim permintaan edit schedule (method patch)
    """
    logger.info(f"Mengirim permintaan edit schedule.")
    try:
        url = f"https://api.upload-post.com/api/schedule/{payload.job_id}"
        headers = {
            "Authorization": f"api_key {settings.UPLOAD_POST_API_KEY}"
        }
        response = requests.patch(
            url,
            headers=headers,
            json={
                "scheduled_date": payload.scheduled_date,
                "caption": payload.caption
            }
        )
        if response.status_code == 200 :
            logger.info(f"Berhasil melakukan edit. Job ID: {payload.job_id}. Caption: {payload.caption}. Upload Schedule: {payload.scheduled_date}")
            return response
        else:
            logger.error(f"Terjadi error saat mengirim permintaan edit ke Upload Post.")
    except Exception as e:
        logger.error("Error Requesting delete schedule.")