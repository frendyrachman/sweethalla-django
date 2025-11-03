# SweetHala - Penjadwal Media Sosial Berbasis AI

SweetHala adalah aplikasi web canggih yang dirancang untuk mengotomatiskan dan menyederhanakan proses penjadwalan konten media sosial. Dibangun dengan Django, aplikasi ini tidak hanya memungkinkan pengguna untuk menjadwalkan postingan ke Instagram dan TikTok, tetapi juga terintegrasi dengan teknologi AI dari OpenAI untuk meningkatkan kualitas konten.

## Fitur Inti

- **Manajemen Jadwal Lengkap**:
  - Buat jadwal postingan dengan mudah melalui form yang intuitif.
  - Lihat semua jadwal aktif dalam satu dasbor yang rapi.
  - Hapus jadwal dari aplikasi lokal dan layanan eksternal secara bersamaan.
- **Integrasi AI untuk Konten**:
  - **AI Image Editor**: Ubah gambar secara otomatis menggunakan prompt teks melalui API OpenAI (gpt-image-1).
  - **AI Caption Generator**: Hasilkan caption media sosial yang kreatif dan relevan untuk gambar Anda menggunakan model GPT-4.
- **Alur Kerja Konfirmasi**: Pengguna dapat meninjau hasil editan gambar dan caption dari AI sebelum mengonfirmasi jadwal akhir.
- **Integrasi API Eksternal**:
  - Terhubung dengan layanan `upload-post.com` untuk mengirim dan mengelola jadwal unggahan.
  - Sinkronisasi data dua arah: jadwal yang dihapus dari layanan eksternal akan terhapus juga dari aplikasi lokal.
- **Penanganan Zona Waktu**: Waktu jadwal secara otomatis dikonversi ke UTC untuk memastikan konsistensi dengan API eksternal.
- **Pembersihan Otomatis**: Jadwal yang sudah lewat tanggalnya akan dihapus secara otomatis untuk menjaga kebersihan data.
- **Antarmuka Dinamis**: Form yang responsif dan interaktif menyesuaikan pilihan input pengguna secara real-time menggunakan JavaScript.

## Alur Kerja Aplikasi

1.  **Pembuatan Jadwal**: Pengguna mengisi form, memilih platform (Instagram/TikTok), waktu, mengunggah media, dan memilih opsi AI (edit gambar atau buat caption).
2.  **Proses AI**: Jika opsi AI dipilih, aplikasi akan mengirim permintaan ke API OpenAI.
3.  **Halaman Konfirmasi**: Pengguna diarahkan ke halaman konfirmasi untuk:
    - Melihat pratinjau gambar hasil editan AI.
    - Melihat dan menyunting caption yang dihasilkan oleh AI.
4.  **Konfirmasi Akhir**: Setelah pengguna menekan "Confirm & Schedule":
    - Data final (gambar dan caption) disimpan di database lokal.
    - Permintaan penjadwalan dikirim ke API eksternal `upload-post.com`.
    - `job_id` dari API eksternal disimpan untuk referensi di masa depan.
5.  **Dasbor Jadwal**: Pengguna melihat daftar semua jadwal yang aktif. Halaman ini secara otomatis melakukan sinkronisasi dengan API eksternal untuk memastikan data selalu up-to-date.

## Teknologi yang Digunakan

- **Backend**: Django
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Integrasi AI**: OpenAI API (DALL-E, GPT-4)
- **Layanan Eksternal**: `upload-post.com` API
- **Tugas Latar Belakang (Desain)**: Dirancang untuk dapat diintegrasikan dengan Celery & Redis untuk tugas asinkron.
- **Deployment (Rekomendasi)**: Gunicorn, Nginx

---

## Pengaturan dan Instalasi

Ada dua cara untuk menjalankan proyek ini: menggunakan Docker (direkomendasikan untuk kemudahan) atau secara manual.

### Menjalankan dengan Docker (Rekomendasi)

Metode ini akan menyiapkan semua yang Anda butuhkan: server web, database PostgreSQL, Redis, dan Celery worker.

**Prasyarat:**
- Docker
- Docker Compose

**Langkah-langkah:**

1.  **Clone Repository**
    ```bash
    git clone https://github.com/your-username/sweethala.git
    cd sweethala
    ```

2.  **Konfigurasi Environment Variables**
    Buat file `.env` di direktori root proyek dan isi dengan variabel yang diperlukan. Gunakan `DATABASE_URL` untuk PostgreSQL yang akan dijalankan oleh Docker.

    ```ini
    # Contoh isi file .env
    SECRET_KEY='ganti-dengan-secret-key-django-anda'
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1,web
    OPENAI_API_KEY='your-openai-api-key'
    UPLOAD_POST_API_KEY='your-upload-post-api-key'
    DATABASE_URL='postgres://sweethala_user:sweethala_password@db:5432/sweethala_db'
    CELERY_BROKER_URL='redis://redis:6379/0'
    CELERY_RESULT_BACKEND='redis://redis:6379/0'
    ```

3.  **Build dan Jalankan Container**
    ```bash
    docker-compose up --build
    ```
    Perintah ini akan membangun image, mengunduh image yang diperlukan (Postgres, Redis), dan menjalankan semua layanan.

4.  **Buat Superuser (Opsional)**
    Buka terminal baru dan jalankan perintah berikut untuk membuat akun admin:
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

5.  **Akses Aplikasi**
    Buka browser Anda dan akses `http://127.0.0.1:8000`.

### Menjalankan Secara Manual (Lokal)

**Prasyarat:**
- Python 3.9+
- PostgreSQL
- Redis

1.  **Clone Repository**
    ```bash
    git clone https://github.com/your-username/sweethala.git
    cd sweethala
    ```

2.  **Buat dan Aktifkan Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instal Dependensi**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi Environment Variables**
    Buat file `.env` dan isi sesuai dengan konfigurasi lokal Anda.

    ```ini
    # Contoh isi file .env untuk lokal
    SECRET_KEY='ganti-dengan-secret-key-django-anda'
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    OPENAI_API_KEY='your-openai-api-key'
    UPLOAD_POST_API_KEY='your-upload-post-api-key'
    DATABASE_URL='postgres://user:password@localhost:5432/your_db_name'
    CELERY_BROKER_URL='redis://localhost:6379/0'
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
    ```

5.  **Jalankan Migrasi dan Buat Superuser**
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
    ```

6.  **Jalankan Layanan**
    Anda perlu menjalankan server Django, Celery worker, dan Redis di terminal terpisah.

    *   **Terminal 1 (Redis):** Pastikan server Redis Anda berjalan.
    *   **Terminal 2 (Celery):**
        ```bash
        celery -A internal_scheduler worker -l info
        ```
    *   **Terminal 3 (Django):**
        ```bash
        python manage.py runserver
        ```

7.  **Akses Aplikasi**
    Buka browser Anda dan akses `http://127.0.0.1:8000`.

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

Buat file `.env` di direktori root proyek (sejajar dengan `manage.py`) dan isi dengan variabel yang diperlukan.

```ini
# Contoh isi file .env
SECRET_KEY='ganti-dengan-secret-key-django-anda'
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

**Jalankan Server Pengembangan Django**
```bash
python manage.py runserver
```
Buka browser Anda dan akses `http://127.0.0.1:8000`.

**Catatan untuk Proses Latar Belakang (Opsional):**
Jika Anda ingin mengimplementasikan tugas asinkron (misalnya, pemanggilan API yang lama), jalankan Celery worker di terminal terpisah.
```bash
celery -A internal_scheduler worker -l info
```

**Terminal 2: Jalankan Server Pengembangan Django**
```bash
python manage.py runserver
```

Buka browser Anda dan akses `http://127.0.0.1:8000`.