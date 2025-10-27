
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
import time
import logging
import os
import base64
import uuid
from openai import OpenAI
from upload_post import UploadPostClient

from .models import Schedule, MediaAsset, ApiScheduleLog
from .forms import ScheduleForm, PLATFORM_CHOICES_FOR_FORM
from .schemas import SchedulePayload, AIEditPayload

# Set up a logger for this module
logger = logging.getLogger(__name__)

# Get OpenAI API Key from env
OPENAI_API_KEY = settings.OPENAI_API_KEY
UPLOAD_POST_API_KEY = settings.UPLOAD_POST_API_KEY

# Mockup API Functions
def ai_edit_content(payload: AIEditPayload, api_key: str):
    """
    Calls the OpenAI gpt-image-1 API to edit an image based on a prompt,
    saves the result to a new file, and returns the new file's path.
    """
    logger.info(f"Memulai proses edit AI untuk file {os.path.basename(payload.media_file_path)}...")
    try:
        client = OpenAI(api_key=api_key)
        with open(payload.media_file_path, "rb") as image_file:
            result = client.images.edit(
                model="gpt-image-1",
                image=image_file,
                prompt=payload.prompt,
                response_format="b64_json"
            )
        logger.info(f"Proses: Berhasil melakukan AI Edit. Melakuakan simpan file ke disk.")
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        # Generate a new unique filename to avoid overwriting
        directory = os.path.dirname(payload.media_file_path)
        original_filename, extension = os.path.splitext(os.path.basename(payload.media_file_path))
        new_filename = f"{original_filename}_edited_{uuid.uuid4().hex[:6]}.png" # DALL-E returns PNG
        new_file_path = os.path.join(directory, new_filename)

        with open(new_file_path, "wb") as f:
            f.write(image_bytes)
            
        logger.info(f"Proses simpan sukses. File baru disimpan sebagai: {new_filename}")
        return new_file_path
    except Exception as e:
        logger.error(f"Gagal melakukan edit AI. Detail: {e}", exc_info=True)
        return None 

def call_upload_post_api_schedule(payload: SchedulePayload, api_key: str):
    client = UploadPostClient(api_key)
    if payload.media_type != 'VIDEO':
        logger.info(f"Proses: Penjadwalan konten gambar ke {payload.platform}...")
        response = client.upload_photos(
            photo_paths=[payload.media_file_path],
            title=payload.caption,
            user="wishtravel",
            platforms=[payload.platform],
            scheduled_date=payload.schedule_time.strftime("%Y-%m-%d")
        ) 
        logger.info(f"Proses sukses. Job ID diterima: {response.job_id}")
        return response
    elif payload.media_type == 'VIDEO':
        logger.info(f"Proses: Penjadwalan konten video ke {payload.platform}...")
        response = client.upload_video(
            video_path=payload.media_file_path,
            title=payload.caption,
            user="wishtravel",
            platforms=[payload.platform],
            scheduled_date=payload.schedule_time.strftime("%Y-%m-%d")
        )
        logger.info(f"Proses sukses. Job ID diterima: {response.job_id}")
        return response
    else:
        logger.error(f"Tipe media tidak valid: {payload.media_type}")
        return None

def get_all_scheduled_jobs(api_key):
    """Show all scheduled jobs."""
    client = UploadPostClient(api_key)
    try:
        print("Mendapatkan daftar postingan yang sudah terjadwal.")
        # Metode yang diasumsikan tersedia di SDK
        scheduled_posts = client.uploadposts.schedule() 
        
        if scheduled_posts:
            print(f"✅ Ditemukan {len(scheduled_posts)} postingan terjadwal:")
            for post in scheduled_posts:
                # Mengakses field penting dari respon
                print("-" * 30)
                print(f"  Job ID: {post.get('job_id')}")
                print(f"  Judul: {post.get('title')}")
                print(f"  Jenis: {post.get('post_type')}")
                print(f"  Jadwal (UTC): {post.get('scheduled_date')}")
                
            # Simpan Job ID pertama untuk contoh berikutnya
            first_job_id = scheduled_posts[0]['job_id']
            print(f"\nID Pekerjaan Pertama: {first_job_id} (untuk demonstrasi edit/cancel)")
            
        else:
            print("ℹ️ Tidak ada postingan yang terjadwalkan saat ini.")

    except Exception as e:
        print(f"❌ Gagal mengambil daftar jadwal: {e}")


def call_upload_post_api_cancel(job_id, api_key):
    """Mengirim cancel request ke API."""
    client = UploadPostClient(api_key)
    

    return True

def ai_generate_caption(media_file_path, api_key):
    """Mocks OpenAI API call for caption generation."""
    logger.info(f"Simulasi: Analisis media di {os.path.basename(media_file_path)} untuk membuat caption...")
    caption = "Contoh caption hasil AI: Momen spesial yang tak terlupakan! ✨ #GeneratedByAI #DjangoScheduler"
    logger.info(f"Simulasi sukses. Caption dihasilkan: '{caption[:30]}...'")
    return caption

# Views
@login_required
def home(request):
    return render(request, 'scheduler/home.html')

@login_required
def create_schedule(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST, request.FILES)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            schedule.save()

            # Simpan file media yang diunggah sebagai MediaAsset
            uploaded_files = request.FILES.getlist('media_files')
            media_paths = []
            for index, f in enumerate(uploaded_files):
                asset = MediaAsset.objects.create(schedule=schedule, file=f, order=index)
                media_paths.append(asset.file.path)

            # Gunakan path file pertama untuk proses AI
            primary_media_path = media_paths[0] if media_paths else None

            # Proses AI (jika diperlukan)
            if schedule.needs_ai_edit and schedule.media_type == 'SINGLE_IMAGE' and primary_media_path:
                edit_payload = AIEditPayload(
                    media_file_path=primary_media_path,
                    prompt=schedule.ai_edit_prompt
                )
                new_media_path = ai_edit_content(edit_payload, settings.OPENAI_API_KEY)
                
                if new_media_path:
                    # Jika edit berhasil, update path media untuk proses selanjutnya
                    primary_media_path = new_media_path
                    # Anda bisa mempertimbangkan untuk menghapus file lama di sini atau nanti

            if schedule.needs_ai_caption and primary_media_path:
                schedule.final_caption = ai_generate_caption(primary_media_path, settings.OPENAI_API_KEY)

            # Panggil API Penjadwalan
            try:
                payload = SchedulePayload(
                    platform=schedule.platform,
                    media_type=schedule.media_type,
                    media_file_path=primary_media_path,  # API mock saat ini hanya handle 1 file
                    schedule_time=schedule.schedule_time,
                    caption=schedule.final_caption
                )
                response = call_upload_post_api_schedule(payload, settings.UPLOAD_POST_API_KEY)
                job_id = response.job_id if response else None
            except Exception as e:
                # Jika validasi Pydantic gagal atau ada error lain
                logger.error(f"Gagal membuat payload atau menjadwalkan: {e}", exc_info=True)
                # Di sini Anda bisa menambahkan error ke form atau message ke user
                job_id = None
            
            if job_id:
                schedule.upload_job_id = job_id
                schedule.is_uploaded = True # Menandakan sudah dijadwalkan via API
                schedule.save()

                # Buat log untuk pemanggilan API
                ApiScheduleLog.objects.create(
                    schedule=schedule,
                    job_id=job_id,
                    schedule_time=schedule.schedule_time,
                    platform=schedule.platform,
                    status='SCHEDULED' # atau status lain dari response jika ada
                )
            
            return redirect('schedule_list')
    else:
        form = ScheduleForm()
    
    return render(request, 'scheduler/schedule_form.html', {'form': form})

@login_required
def schedule_list(request):
    schedules = Schedule.objects.filter(user=request.user).order_by('-schedule_time')
    return render(request, 'scheduler/schedule_list.html', {'schedules': schedules})

@login_required
def open_schedule_list(request):
    logs = ApiScheduleLog.objects.filter(schedule__user=request.user).order_by('-schedule_time')
    return render(request, 'scheduler/open_schedule_list.html', {'logs': logs})


@login_required
def delete_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    if request.method == 'POST':
        # Panggil API pembatalan
        if schedule.upload_job_id:
            call_upload_post_api_cancel(schedule.upload_job_id, settings.UPLOAD_POST_API_KEY)
        
        # Hapus objek dari DB (ini juga akan menghapus file media karena override di model)
        schedule.delete()
        
        return redirect('schedule_list')
    
    # Jika bukan POST, bisa tampilkan halaman konfirmasi (opsional)
    return redirect('schedule_list')

# Authentication Views
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'scheduler/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
