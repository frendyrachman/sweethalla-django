from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import ScheduleForm
from .models import Schedule, MediaAsset
from django.utils import timezone
from .ai_service import run_ai_tasks_for_schedule
from .upload_post_service import schedule_post_upload, delete_upload_schedule, get_schedule

# Authentication Views
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('scheduler:home')
    else:
        form = AuthenticationForm()
    return render(request, 'scheduler/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('scheduler:login')

# Landing Page View (Public)
def landing_page_view(request):
    """
    Menampilkan halaman landing page publik untuk customer.
    """
    return render(request, 'scheduler/landing_page.html')

# Schedule CRUD Views
@login_required
def create_schedule(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST, request.FILES)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            schedule.save()

            files = request.FILES.getlist('media_files')
            for i, f in enumerate(files):
                MediaAsset.objects.create(schedule=schedule, file=f, order=i)

            # Jika ada tugas AI, arahkan ke view pemrosesan AI dulu
            if schedule.needs_ai_edit or schedule.needs_ai_caption:
                return redirect('scheduler:run_ai_and_confirm', schedule_id=schedule.id)
            else:
                # Jika tidak, langsung ke halaman konfirmasi
                return redirect('scheduler:schedule_confirmation', schedule_id=schedule.id)
    else:
        form = ScheduleForm()
    return render(request, 'scheduler/schedule_form.html', {'form': form})

@login_required
def schedule_list(request):
    # Langkah 1: Hapus jadwal lokal yang sudah lewat tanggalnya
    now = timezone.now()
    past_schedules = Schedule.objects.filter(user=request.user, schedule_time__lt=now)
    if past_schedules.exists():
        past_schedules.delete()

    # Langkah 2 (Baru): Sinkronisasi dengan data dari API eksternal
    # Ambil daftar jadwal dari API upload-post
    remote_schedules_data = get_schedule() # Memanggil fungsi baru Anda
    if remote_schedules_data:
        # Dapatkan daftar semua job_id yang ada di API eksternal
        remote_job_ids = {item.get('job_id') for item in remote_schedules_data if item.get('job_id')}
        
        # Dapatkan semua jadwal lokal yang memiliki job_id
        local_schedules_with_jobs = Schedule.objects.filter(user=request.user).exclude(upload_job_id__isnull=True).exclude(upload_job_id__exact='')
        
        # Hapus jadwal lokal yang job_id-nya tidak lagi ditemukan di API eksternal
        schedules_to_delete = local_schedules_with_jobs.exclude(upload_job_id__in=remote_job_ids)
        if schedules_to_delete.exists():
            schedules_to_delete.delete()

    # Langkah 3: Ambil daftar jadwal final dari database lokal untuk ditampilkan
    schedules = Schedule.objects.filter(user=request.user).order_by('-schedule_time')
    return render(request, 'scheduler/schedule_list.html', {'schedules': schedules})

@login_required
def delete_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    if request.method == 'POST':
        # Jika jadwal ini memiliki job_id dari API, panggil service untuk menghapusnya di sana dulu
        if schedule.upload_job_id:
            delete_upload_schedule(schedule.upload_job_id) # Memanggil fungsi baru Anda
        
        # Hapus jadwal dari database lokal
        schedule.delete()
        return redirect('scheduler:schedule_list')
    return redirect('scheduler:schedule_list')

# Home and Preview/Process Views
def home(request):
    if request.user.is_authenticated:
        return redirect('scheduler:schedule_list')
    return redirect('scheduler:login')

@login_required
def run_ai_and_confirm(request, schedule_id):
    """
    Menjalankan tugas AI yang diperlukan, menyimpan hasilnya ke session,
    dan kemudian mengarahkan ke halaman konfirmasi.
    """
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)

    # Jalankan tugas AI
    ai_results = run_ai_tasks_for_schedule(schedule)

    # Simpan hasil AI ke session untuk digunakan di halaman konfirmasi dan saat proses
    request.session['ai_results'] = ai_results
    
    # Arahkan ke halaman konfirmasi untuk ditampilkan ke pengguna
    return redirect('scheduler:schedule_confirmation', schedule_id=schedule.id)

@login_required
def schedule_confirmation(request, schedule_id):
    """
    Hanya menampilkan halaman konfirmasi dengan data dari schedule dan session.
    """
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    ai_results = request.session.get('ai_results', {})

    # Atur atribut sementara pada objek schedule untuk pratinjau di template
    schedule.ai_generated_caption = ai_results.get('ai_generated_caption')
    edited_media_path = ai_results.get('edited_media_url')
    
    # Di sini kita tidak perlu lagi mengatur primary_asset.edited_file.name
    # karena kita akan menggunakan URL langsung dari ai_results di template.

    return render(request, 'scheduler/schedule_confirmation.html', {
        'schedule': schedule,
        'ai_results': ai_results, # Kirim juga ai_results ke template
    })


@login_required
def process_confirmation(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    
    if request.method == 'POST':
        try:
            if 'confirm' in request.POST:
                # Ambil hasil AI dari session
                ai_results = request.session.get('ai_results', {})
    
                # Simpan caption final dan ubah status
                final_caption = request.POST.get('final_caption', schedule.caption)
                schedule.caption = final_caption
                
                # Simpan hasil AI secara permanen
                if ai_results.get('ai_generated_caption'):
                    schedule.ai_generated_caption = ai_results['ai_generated_caption']
                
                edited_media_path = ai_results.get('edited_media_url')
                if edited_media_path:
                    primary_asset = schedule.get_primary_media_asset()
                    if primary_asset:
                        primary_asset.edited_file.name = ai_results['edited_media_url'].split('/media/')[-1]
                        primary_asset.save()
    
                schedule.status = 'CONFIRMED'
                schedule.save()
                schedule_post_upload(schedule) # Panggil service untuk mengirim ke API eksternal
                return redirect('scheduler:schedule_list')
            elif 'cancel' in request.POST:
                schedule.delete()
                return redirect('scheduler:schedule_list')
        finally:
            # Selalu hapus session setelah POST (baik confirm maupun cancel)
            # Blok finally ini akan dieksekusi sebelum fungsi me-return redirect.
            if 'ai_results' in request.session:
                del request.session['ai_results']
            
    # Jika request bukan POST, arahkan kembali ke halaman konfirmasi.
    return redirect('scheduler:schedule_confirmation', schedule_id=schedule.id)
