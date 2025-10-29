from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import ScheduleForm
from .models import Schedule, MediaAsset
from .ai_service import run_ai_tasks_for_schedule
from .upload_post_service import schedule_post_upload

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

            if schedule.needs_ai_caption or schedule.needs_ai_edit:
                return redirect('scheduler:ai_preview', schedule_id=schedule.id)
            else:
                return redirect('scheduler:schedule_preview', schedule_id=schedule.id)
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
        schedule.delete()
        return redirect('scheduler:schedule_list')
    return redirect('scheduler:schedule_list')

# Home and Preview/Process Views
def home(request):
    if request.user.is_authenticated:
        return redirect('scheduler:schedule_list')
    return redirect('scheduler:login')

@login_required
def schedule_preview(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    return render(request, 'scheduler/schedule_preview.html', {'schedule': schedule})

@login_required
def ai_preview(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    ai_results = run_ai_tasks_for_schedule(schedule) # Ini sekarang mengembalikan dictionary

    # Simpan hasil AI ke model SEBELUM me-render template
    schedule.ai_generated_caption = ai_results.get('ai_generated_caption')
    
    edited_media_path = ai_results.get('edited_media_url') # Ini sekarang berisi path file
    primary_asset = schedule.get_primary_media_asset()
    if edited_media_path and primary_asset:
        # Tetapkan path file yang diedit ke field FileField
        primary_asset.edited_file.name = edited_media_path
        primary_asset.save() # Simpan perubahan pada objek MediaAsset

    schedule.save() # Simpan perubahan pada objek Schedule (untuk caption)
    
    return render(request, 'scheduler/ai_preview.html', {
        'schedule': schedule,
        # Template sekarang akan mengambil data yang sudah tersimpan dari objek 'schedule'
    })

@login_required
def confirm_ai_result(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    
    if request.method == 'POST':
        # Cek tombol mana yang ditekan pada form di template
        if 'confirm' in request.POST:
            # Jika pengguna konfirmasi, simpan caption dan lanjut
            ai_caption = request.POST.get('ai_caption')
            schedule.ai_generated_caption = ai_caption
            schedule.save()
            return redirect('scheduler:schedule_preview', schedule_id=schedule.id)
        
        elif 'cancel' in request.POST:
            # Jika pengguna membatalkan, hapus jadwal dan kembali ke daftar
            schedule.delete()
            return redirect('scheduler:schedule_list')

    return redirect('scheduler:ai_preview', schedule_id=schedule.id)

@login_required
def process_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    if request.method == 'POST':
        schedule.status = 'CONFIRMED'
        schedule.save()
        schedule_post_upload(schedule)
        return redirect('scheduler:schedule_list')
    return redirect('scheduler:schedule_preview', schedule_id=schedule.id)
