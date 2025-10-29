from django import forms
from .models import Schedule

PLATFORM_CHOICES_FOR_FORM = [
    ('IG', 'Instagram'),
    ('TIKTOK', 'TikTok'),
]

class ScheduleForm(forms.ModelForm):
    platform = forms.MultipleChoiceField(choices=PLATFORM_CHOICES_FOR_FORM, widget=forms.CheckboxSelectMultiple, required=True)
    media_files = forms.FileField(required=True, label="Media File(s)")

    class Meta:
        model = Schedule
        fields = [
            'platform', 'media_type', 'content_type', 'schedule_time', 'needs_ai_edit',
            'ai_edit_prompt', 'needs_ai_caption', 'caption'
        ]
        widgets = {
            'schedule_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ai_edit_prompt': forms.Textarea(attrs={'rows': 3}),
            'caption': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ai_edit_prompt'].required = False
        self.fields['content_type'].required = False # Opsional, tergantung logika bisnis
        self.fields['caption'].required = False
        self.fields['caption'].label = "Manual Caption"

    def clean_platform(self):
        """
        Mengonversi list dari checkbox (e.g., ['IG', 'TIKTOK']) menjadi
        satu nilai yang bisa disimpan di model ('IG', 'TIKTOK', atau 'BOTH').
        """
        platforms = self.cleaned_data.get('platform')
        if len(platforms) == 2:
            return 'BOTH'
        elif len(platforms) == 1:
            return platforms[0]
        # Jika tidak ada yang dipilih, validasi form akan gagal karena `required=True`
        return None

    def clean(self):
        cleaned_data = super().clean()
        media_type = cleaned_data.get("media_type")
        # Akses file dari self.files karena tidak terikat ke model
        media_files = self.files.getlist('media_files')

        if not media_files:
            self.add_error('media_files', 'This field is required.')

        if media_type == 'SINGLE_IMAGE' and len(media_files) > 1:
            self.add_error('media_files', 'Untuk "Single Image", Anda hanya bisa mengunggah satu file.')

        if media_type == 'VIDEO' and len(media_files) > 1:
            self.add_error('media_files', 'Untuk "Video", Anda hanya bisa mengunggah satu file.')

        if media_type == 'CAROUSEL' and len(media_files) < 2:
            self.add_error('media_files', 'Untuk "Carousel", Anda harus mengunggah minimal dua gambar.')

        return cleaned_data
