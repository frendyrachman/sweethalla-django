# SweetHala - Social Media Scheduler

SweetHala adalah aplikasi web penjadwalan konten media sosial yang dibangun menggunakan Django. Aplikasi ini memungkinkan pengguna untuk menjadwalkan postingan gambar dan video ke platform seperti Instagram dan TikTok, dengan fitur tambahan yang didukung oleh AI.

## Fitur Utama

- **Manajemen Jadwal**: Buat, lihat, dan hapus jadwal postingan.
- **Autentikasi Pengguna**: Sistem login dan logout yang aman untuk melindungi data pengguna.
- **Dukungan Multi-platform**: Jadwalkan konten untuk Instagram, TikTok, atau keduanya.
- **Integrasi AI (Mock)**:
  - **AI Image Editor**: Edit gambar secara otomatis berdasarkan prompt teks menggunakan DALL-E 2.
  - **AI Caption Generator**: Buat caption yang menarik secara otomatis dari konten media.
- **Proses Latar Belakang**: Dirancang untuk menggunakan Celery untuk menangani tugas-tugas berat seperti pemanggilan API dan pemrosesan file.
- **Antarmuka Dinamis**: Form yang interaktif dan responsif dibangun dengan bantuan JavaScript.

## Teknologi yang Digunakan

- **Backend**: Django
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Tugas Latar Belakang**: Celery & Redis
- **API Eksternal**: OpenAI
- **Deployment (Rekomendasi)**: Gunicorn, Nginx

---

## Pengaturan dan Instalasi Lokal

Ikuti langkah-langkah berikut untuk menjalankan proyek ini di lingkungan lokal Anda.

### 1. Prasyarat

- Python 3.10+
- Git
- Redis (terinstal dan berjalan di sistem Anda)

### 2. Clone Repository

```bash
git clone https://github.com/your-username/sweethala.git
cd sweethala
```

### 3. Buat dan Aktifkan Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Instal Dependensi

```bash
pip install -r requirements.txt
```

### 5. Konfigurasi Environment Variables

Buat file `.env` di direktori root proyek (sejajar dengan `manage.py`) dan isi dengan variabel yang diperlukan. Anda bisa menyalin dari `.env.example`.

```ini
# Contoh isi file .env
SECRET_KEY='your-django-secret-key'
DEBUG=True
OPENAI_API_KEY='your-openai-api-key'
UPLOAD_POST_API_KEY='your-upload-post-api-key'
DATABASE_URL='sqlite:///db.sqlite3' # Untuk development
# DATABASE_URL='postgres://user:password@host:port/dbname' # Untuk production
```

### 6. Jalankan Migrasi Database

```bash
python manage.py migrate
```

### 7. Buat Superuser

```bash
python manage.py createsuperuser
```

### 8. Jalankan Server

Buka dua terminal terpisah.

**Terminal 1: Jalankan Celery Worker**
```bash
celery -A internal_scheduler worker -l info
```

**Terminal 2: Jalankan Server Pengembangan Django**
```bash
python manage.py runserver
```

Buka browser Anda dan akses `http://127.0.0.1:8000`.