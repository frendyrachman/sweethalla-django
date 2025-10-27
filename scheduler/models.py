from django.db import models
from django.contrib.auth.models import User
import os

class Schedule(models.Model):
    PLATFORM_CHOICES = [
        ('IG', 'Instagram'),
        ('TIKTOK', 'TikTok'),
        ('BOTH', 'Both'),
    ]
    MEDIA_TYPE_CHOICES = [
        ('SINGLE_IMAGE', 'Single Image'),
        ('CAROUSEL', 'Carousel'),
        ('VIDEO', 'Video'),
    ]
    CONTENT_TYPE_CHOICES = [
        ('REELS', 'Reels'),
        ('STORIES', 'Stories'),
        ('SINGLE_POST', 'Single Post'),
        ('CAROUSEL_POST', 'Carousel Post'), # Menggunakan nama yang berbeda dari media_type
        ('TIKTOK_VIDEO', 'TikTok Video'), # Menggunakan nama yang berbeda dari media_type
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    # Field baru ditambahkan di sini
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, blank=True, null=True)
    schedule_time = models.DateTimeField()
    needs_ai_edit = models.BooleanField(default=False)
    ai_edit_prompt = models.TextField(blank=True, null=True)
    needs_ai_caption = models.BooleanField(default=False)
    final_caption = models.TextField(blank=True, null=True)
    upload_job_id = models.CharField(max_length=255, blank=True, null=True)
    is_uploaded = models.BooleanField(default=False)

    def get_primary_media_asset(self):
        """Mengambil aset media pertama, berguna untuk thumbnail atau single post."""
        return self.media_assets.first()

    def __str__(self):
        return f'{self.user.username} - {self.get_platform_display()} at {self.schedule_time}'


class MediaAsset(models.Model):
    """Model untuk menyimpan setiap file media yang terkait dengan sebuah jadwal."""
    schedule = models.ForeignKey(Schedule, related_name='media_assets', on_delete=models.CASCADE)
    file = models.FileField(upload_to='media/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Media for Schedule ID: {self.schedule.id} - {os.path.basename(self.file.name)}"

    def delete(self, *args, **kwargs):
        # Hapus file fisik saat objek MediaAsset dihapus
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)


class ApiScheduleLog(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='api_logs')
    job_id = models.CharField(max_length=255)
    schedule_time = models.DateTimeField()
    platform = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for Job ID: {self.job_id}"
