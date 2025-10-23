
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

from .models import Schedule, MediaAsset
from .forms import ScheduleForm

# Set up a logger for this module
logger = logging.getLogger(__name__)

# Get OpenAI API Key from env
OPENAI_API_KEY = settings.OPENAI_API_KEY
UPLOAD_POST_API_KEY = settings.UPLOAD_POST_API_KEY

# Mockup API Functions
def ai_edit_content(media_file_path, prompt, api_key):
    """
    Calls the OpenAI gpt-image-1 API to edit an image based on a prompt,
    saves the result to a new file, and returns the new file's path.
    """
    logger.info(f"Memulai proses edit AI untuk file {os.path.basename(media_file_path)}...")
    try:
        client = OpenAI(api_key=api_key)
        
        with open(media_file_path, "rb") as image_file:
            result = client.images.edit(
                model="gpt-image-1",
                image=image_file,
                prompt=prompt,
                response_format="b64_json"
            )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        # Generate a new unique filename to avoid overwriting
        directory = os.path.dirname(media_file_path)
        original_filename, extension = os.path.splitext(os.path.basename(media_file_path))
        new_filename = f"{original_filename}_edited_{uuid.uuid4().hex[:6]}.png" # DALL-E returns PNG
        new_file_path = os.path.join(directory, new_filename)

        with open(new_file_path, "wb") as f:
            f.write(image_bytes)
            
        logger.info(f"Proses edit AI sukses. File editan disimpan sebagai: {new_filename}")
        return new_file_path
    except Exception as e:
        logger.error(f"Gagal melakukan edit AI. Detail: {e}", exc_info=True)
        return None # Return None to indicate failure

def call_upload_post_api_schedule(image_path, schedule_data, api_key):
    # client = UploadPostClient(UPLOAD_POST_API_KEY)
    # response = client.upload_video(
    #     video_path="/path/to/video.mp4",
    #     title="My Awesome Video",
    #     user="testuser",
    #     platforms=["tiktok", "instagram"]
    # )
    logger.info(f"Simulasi: Penjadwalan konten ke {schedule_data['platform']}...")
    job_id = "mock_job_" + str(int(time.time()))
    logger.info(f"Simulasi sukses. Job ID diterima: {job_id}")
    return job_id

def call_upload_post_api_cancel(job_id, api_key):
    """Mocks API call to Upload-Post.com for cancellation."""
    logger.info(f"Simulasi: Pembatalan jadwal dengan Job ID: {job_id}...")
    logger.info("Simulasi sukses. Jadwal dibatalkan.")
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
                new_media_path = ai_edit_content(primary_media_path, schedule.ai_edit_prompt, settings.OPENAI_API_KEY)
                
                if new_media_path:
                    # Jika edit berhasil, update path media untuk proses selanjutnya
                    primary_media_path = new_media_path
                    # Anda bisa mempertimbangkan untuk menghapus file lama di sini atau nanti

            if schedule.needs_ai_caption and primary_media_path:
                schedule.final_caption = ai_generate_caption(primary_media_path, settings.OPENAI_API_KEY)

            # Panggil API Penjadwalan
            schedule_data = {
                'platform': schedule.platform,
                'media_file': primary_media_path, # API mock saat ini hanya handle 1 file
                'schedule_time': schedule.schedule_time,
                'caption': schedule.final_caption
            }
            job_id = call_upload_post_api_schedule(schedule_data, settings.UPLOAD_POST_API_KEY)
            
            schedule.upload_job_id = job_id
            schedule.is_uploaded = True # Menandakan sudah dijadwalkan via API
            schedule.save()
            
            return redirect('schedule_list')
    else:
        form = ScheduleForm()
    
    return render(request, 'scheduler/schedule_form.html', {'form': form})

@login_required
def schedule_list(request):
    schedules = Schedule.objects.filter(user=request.user).order_by('-schedule_time')
    return render(request, 'scheduler/schedule_list.html', {'schedules': schedules})

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
