# Product Requirement Document (PRD)
**Project Name:** AI Metal Sheet Monitoring System (Detection, Counting, & Defect Analysis)
**Target Hardware:** NVIDIA Jetson Orin Nano (8GB)
**Version:** 1.0
**Date:** 17 Desember 2024

---

## 1. Executive Summary
Sistem ini adalah solusi berbasis *Computer Vision* yang bertujuan untuk memantau proses *stacking* (penumpukan) plat logam (*metal sheet*). Sistem akan melakukan penghitungan otomatis (*counting*) secara *real-time* saat plat diletakkan ke dalam wadah, serta menyediakan fitur analisis lanjutan untuk mendeteksi cacat (*defect segmentation*) dan pengukuran dimensi (*dimension measurement*) berdasarkan gambar yang di-*capture* dari proses counting tersebut.

## 2. User Personas
1.  **Operator/QA:** Mengawasi proses counting berjalan, menerima notifikasi jika jumlah sesi tidak sesuai, dan melakukan analisis cacat pada gambar hasil capture.
2.  **Supervisor:** Melihat laporan data log (JSON) dan rekapitulasi produksi.

## 3. Technical Architecture & AI Strategy

Mengingat keterbatasan *resource* pada **Jetson Orin Nano (8GB)** dan kebutuhan fitur yang spesifik, arsitektur AI akan dibagi menjadi dua *pipeline*:

### A. Pipeline 1: Real-time Detection & Counting (Ringan)
* **Model:** **YOLOv8** atau **YOLO11** (Versi Nano atau Small).
* **Tujuan:** Mendeteksi keberadaan *Metal Sheet* secara cepat dan akurat.
* **Dataset:** Custom dataset atau transfer learning dari COCO/OpenImages (kelas *sheet/plate*).
* **Alasan:** Latency rendah (<30ms) diperlukan untuk monitoring *live* RTSP.

### B. Pipeline 2: Post-Processing Defect & Dimension (Berat)
* **Trigger:** Dijalankan secara *asynchronous* atau *on-demand* di halaman terpisah menggunakan gambar yang sudah di-*capture*.
* **Defect Locator (Model A):** **YOLOv8/11** (trained on **NEU-DET** dataset). Bertugas mencari kotak pembatas (*bounding box*) area cacat (scratches, patches, inclusion).
* **Defect Segmentor (Model B):** **SAM 2 (Segment Anything Model 2)**.
    * *Catatan:* SAM 2 lebih efisien daripada SAM 3 (belum rilis publik stabil) dan memiliki varian "Tiny/Small" yang kompatibel dengan Jetson.
    * *Workflow:* Box dari Model A menjadi "Prompt" otomatis untuk Model B agar SAM 2 melakukan *cropping* presisi mengikuti bentuk cacat.

---

## 4. Functional Requirements

### 4.1. Fitur Utama: Real-time Counting & Capture
**Deskripsi:** Halaman utama dashboard yang menampilkan *video feed* dan status penghitungan.

* **Input Source:**
    * RTSP Stream (IP Camera).
    * Upload Video File (untuk testing/simulasi).
* **Counting Logic (Stacking Flow):**
    1.  **State 0 (Empty/Stable):** Kamera melihat tumpukan lama atau wadah kosong.
    2.  **State 1 (Motion/Occlusion):** Tangan operator/mesin masuk membawa plat (Area of Interest berubah drastis).
    3.  **State 2 (New Object):** Tangan keluar, gambar kembali stabil.
    4.  **Verification:** Sistem mendeteksi *confidence* "Metal Sheet" tinggi.
    5.  **Action:**
        * Counter +1.
        * **Auto-Capture:** Simpan *frame* saat ini ke folder `Session_ID/`.
* **Session Management:**
    * Input: `Session Name`, `Max Count Target`.
    * Output: `Current Count`.
    * **Alert System:** Jika sesi diakhiri (tombol "Finish Session" ditekan) dan `Current Count` != `Max Count Target`, mainkan *Sound Alert* (Sound A untuk kurang, Sound B untuk lebih).

### 4.2. Fitur: Defect Detection (Analisis Cacat)
**Deskripsi:** Halaman untuk memproses gambar hasil capture per sesi.

* **Workflow:**
    1.  User memilih folder Sesi.
    2.  Sistem me-load gambar satu per satu (atau batch).
    3.  **Backend Process:**
        * Jalankan **YOLO (NEU-DET)** untuk mendeteksi *Scratches*, *Inclusions*, *Patches*.
        * Dapatkan koordinat Bounding Box [x1, y1, x2, y2].
        * Kirim koordinat tersebut sebagai *Prompt* ke **SAM 2**.
        * SAM 2 menghasilkan *Mask* (area pixel presisi).
    4.  **Output:**
        * Gambar asli dengan *overlay* mask cacat.
        * **Crop Region:** Simpan potongan gambar area cacat saja (format `.png` atau `.jpg`).
        * **Log Data:** Simpan koordinat dan jenis cacat ke JSON.

### 4.3. Fitur: Dimension Measurement
**Deskripsi:** Mengukur panjang dan lebar metal sheet.

* **Metode:** **Pixel-to-Metric Ratio (Fixed Geometry)**.
* **Logic:**
    1.  Karena kamera statis, kita tentukan nilai konstanta `K` (misal: 1 pixel = 0.5 mm).
    2.  Deteksi kontur terbesar (Metal Sheet).
    3.  Hitung *Rotated Bounding Box* (untuk menangani jika plat diletakkan miring).
    4.  Hitung Panjang & Lebar dalam pixel dikali `K`.
* **Constraint (Isu Parallax):**
    * Karena plat ditumpuk (*stacked*), plat paling atas akan lebih dekat ke kamera dibanding plat paling bawah.
    * *Mitigasi:* Jika tumpukan tidak terlalu tinggi (< 20cm), toleransi error mungkin masih diterima. Jika tumpukan tinggi, perlu input manual "Estimasi tinggi tumpukan" untuk kompensasi rumus, atau terima margin error sekitar 1-5%.

### 4.4. Dashboard & Reporting
* Menampilkan **Summary Object Count** per sesi.
* Log Data disimpan dalam format JSON.
    * Struktur: `{"session_id": "A1", "timestamp": "...", "count": 50, "defects_found": [{"type": "scratch", "file": "crop_01.png"}]}`

---

## 5. Non-Functional Requirements (NFR)

1.  **Environment (Lingkungan):**
    * Pencahayaan terkontrol (Diffused Light) untuk meminimalisir refleksi pada permukaan *matte*.
    * Kamera tegak lurus (Top-Down View).
2.  **Performance:**
    * Counting Latency: < 500ms setelah objek stabil.
    * Accuracy Counting: > 98% (dengan asumsi tidak ada *double feeding* yang sangat cepat).
3.  **Hardware Constraint:**
    * Aplikasi harus memanajemen VRAM Jetson Orin Nano (8GB).
    * *Strategy:* Saat fitur Counting aktif, model SAM 2 harus di-*unload* dari memori. Saat fitur Defect aktif, model Counting bisa di-*pause*.

---

## 6. Development Roadmap & Dataset Recommendation

### Tahap 1: Setup & Dataset
* **Hardware Setup:** Install JetPack 6.x pada Jetson Orin Nano.
* **Dataset Collection:**
    * Untuk Counting: Ambil 100-200 foto metal sheet di wadah (variasikan posisi). Labeling menggunakan Roboflow (Class: `metal_sheet`).
    * Untuk Defect: Download dataset **NEU-DET** (Northeastern University Surface Defect Database). Dataset ini berisi 6 jenis cacat permukaan baja (*scratches, patches, crazing, pitted, inclusion, rolled-in scale*). Gunakan ini untuk melatih YOLO Defect Locator.

### Tahap 2: Core Development (Counting)
* Training YOLOv8 Nano untuk deteksi metal sheet.
* Implementasi logika *Counting* & *Session Management*.
* Integrasi RTSP & Auto-Capture.

### Tahap 3: Advanced Features (SAM 2 & Dimension)
* Install **SAM 2** (gunakan versi *lightweight* atau *converted ONNX* agar ringan di Jetson).
* Buat pipeline: Gambar Capture -> YOLO Detect Defect -> Box Prompt -> SAM 2 Segment -> Crop & Save.
* Implementasi algoritma OpenCV untuk pengukuran dimensi.

### Tahap 4: Integration & UI
* Membangun Dashboard (User merekomendasikan berbasis Web/Desktop, misal Python Streamlit atau PyQt untuk performa lokal yang baik di Jetson).
* Testing akurasi perhitungan tumpukan.

---

### Catatan Khusus untuk Developer:
> **Tentang SAM 2 vs SAM 3:**
> Saat ini, SAM 2 adalah versi stabil terbaru dari Meta AI yang mendukung video dan gambar dengan performa jauh lebih cepat dibanding SAM 1. SAM 3 belum menjadi standar industri yang rilis publik secara luas untuk *deployment* edge. **Rekomendasi kuat:** Gunakan **SAM 2** (varian Tiny/Small) karena sudah mendukung *promptable segmentation* yang dibutuhkan fitur Defect Detection Anda dan lebih ramah untuk Jetson Orin Nano.

---

Tentu, ini adalah revisi bagian **Section 6 (Technology Stack)** dan **Section 8 (Project Structure)** pada PRD Anda.

Perubahan ini mengubah arsitektur dari *Decoupled* (FastAPI + React) menjadi **Monolithic** (Flask + Jinja2 Templates). Pendekatan ini **sangat efisien** untuk deployment di *Edge Device* (Jetson) karena mengurangi overhead komunikasi antar-container dan menyederhanakan proses development.

---

## 6. Technology Stack & Frameworks (Revisi)

Pemilihan stack disesuaikan untuk arsitektur *monolithic* yang ringan, di mana backend dan frontend disajikan oleh satu server aplikasi Python.

### A. Core Application (Backend & Server)

* **Language:** Python 3.10+
* **Web Framework:** **Flask**.
* *Alasan:* Ringan, fleksibel, dan sangat matang (*mature*). Flask memiliki dukungan bawaan yang sangat baik untuk *template rendering* (Jinja2) dan manajemen *static files*, membuatnya ideal untuk aplikasi *single-deployment* di Jetson.


* **Concurrency Strategy:** **Threading / Gevent**.
* *Penting:* Karena Flask bersifat *synchronous* secara default, kita harus menjalankannya dengan mode `threaded=True` atau menggunakan WSGI server seperti `Gunicorn` dengan *worker threads* agar *Video Streaming* (RTSP) tidak memblokir API counting.



### B. Frontend (Presentation Layer)

* **Architecture:** **Server-Side Rendering (SSR)** dengan **Static Templates**.
* **Templating Engine:** **Jinja2** (Bawaan Flask).
* Digunakan untuk merender struktur HTML dasar dan menyisipkan data awal (seperti nama sesi) langsung dari Python.


* **Styling:** **Tailwind CSS**.
* Menggunakan pendekatan *Utility-First* untuk mempercepat UI design tanpa menulis file CSS manual.
* *Deployment:* Menggunakan file script Tailwind standalone (local JS) atau CDN (jika ada internet), atau lebih baik lagi: *pre-compiled CSS* agar bisa berjalan 100% offline.


* **Interactivity:** **Vanilla JavaScript (ES6+)**.
* Tanpa framework berat (No React/Vue).
* Menggunakan `fetch()` API untuk polling data status counter secara *asynchronous*.
* Menggunakan manipulasi DOM sederhana (`document.getElementById`) untuk update angka counter dan notifikasi.


* **Video Streaming:** **MJPEG (Motion JPEG)**.
* Streaming langsung dari route Flask menggunakan `multipart/x-mixed-replace`. Ini metode standar yang sangat kompatibel dengan tag HTML `<img>`.



### C. Database & Storage

* **Database:** **SQLite**.
* Disimpan sebagai file lokal (misal: `production.db`). Tidak memerlukan service database terpisah.


* **Storage:** Local File System (`static/captures/`).

---

## 8. Directory Structure (Revisi)

Struktur proyek disederhanakan. Folder `frontend` dihapus dan digabungkan ke dalam struktur standar Flask (`templates` dan `static`).

**Nama Proyek:** `metal-sheet-monitor-flask`

```text
metal-sheet-monitor-flask/
├── 📂 app/                         # Source code utama aplikasi
│   ├── __init__.py                 # Inisialisasi Flask App & Config
│   ├── 📂 routes/                  # Controller/View Functions
│   │   ├── __init__.py
│   │   ├── main_routes.py          # Render halaman HTML (Home, Analysis)
│   │   ├── api_routes.py           # Endpoint JSON (Counting status, Control)
│   │   └── video_routes.py         # Endpoint Streaming (MJPEG Generator)
│   ├── 📂 services/                # Logika Bisnis & AI (The "Brain")
│   │   ├── camera_manager.py       # Handle OpenCV VideoCapture
│   │   ├── ai_inference.py         # Wrapper YOLO & SAM 2
│   │   ├── counting_logic.py       # State machine stacking
│   │   └── defect_analysis.py      # Logic post-processing defect
│   ├── 📂 static/                  # Aset Statis (CSS, JS, Images)
│   │   ├── 📂 css/
│   │   │   └── style.css           # Output build Tailwind (atau custom css)
│   │   ├── 📂 js/
│   │   │   ├── dashboard.js        # Logic JS untuk halaman Monitoring
│   │   │   └── analysis.js         # Logic JS untuk halaman Defect
│   │   ├── 📂 lib/                 # Library 3rd party (Tailwind Script offline)
│   │   └── 📂 captures/            # [Generated] Hasil capture foto disimpan di sini
│   │       └── session_batch_A/
│   ├── 📂 templates/               # File HTML (Jinja2)
│   │   ├── base.html               # Layout utama (Navbar, Footer, Import CSS/JS)
│   │   ├── dashboard.html          # Halaman 1: Live Monitor
│   │   ├── analysis.html           # Halaman 2: Gallery & Defect Check
│   │   └── settings.html           # Halaman 3: Konfigurasi
│   ├── 📂 models/                  # Database Models
│   │   └── database.py             # SQLite setup
│   └── config.py                   # Konfigurasi Flask (Secret Key, Path)
│
├── 📂 weights/                     # Model AI (.pt)
│   ├── yolo_counting.pt
│   └── sam2_tiny.pt
│
├── Dockerfile                      # Build image (Python + Flask + AI Libs)
├── docker-compose.yml              # Run container
├── requirements.txt                # Dependency (Flask, Ultralytics, OpenCV)
├── run.py                          # Entry point (python run.py)
└── .env                            # Environment Variables

```

---

### Keuntungan Perubahan Ini:

1. **Akses Gambar Langsung:** Karena frontend dan backend berada di satu domain dan server yang sama, menampilkan gambar hasil capture di HTML sangat mudah. Cukup panggil `<img src="{{ url_for('static', filename='captures/img1.jpg') }}">`. Tidak perlu setup CORS atau file server terpisah.
2. **Tailwind Offline:** Anda bisa mendownload file script Tailwind (atau generate CSS-nya) dan meletakkannya di folder `app/static/lib/`. Ini menjamin tampilan dashboard tetap bagus meskipun Jetson tidak terkoneksi internet (Intranet pabrik).
3. **Low Latency:** Mengurangi hop jaringan antar container frontend dan backend.

Berikut adalah revisi teknis untuk bagian **Penjelasan Folder Kunci** hingga strategi **Deployment Docker**, yang telah disesuaikan sepenuhnya untuk arsitektur **Monolithic (Flask + Jinja2)** pada Jetson Orin Nano.

---

### Penjelasan Folder Kunci untuk Developer

Karena kita beralih ke struktur Monolithic, kita tidak lagi memisahkan `backend` dan `frontend`. Semua logika berada dalam satu konteks aplikasi.

1. **`app/services/` (The "Brain")**
Ini adalah lapisan logika yang terpisah dari *routing* web.
* **`camera_manager.py`**: Menangani koneksi RTSP menggunakan OpenCV. Harus berjalan di *thread* terpisah agar tidak membekukan UI Flask.
* **`ai_inference.py`**: Wrapper untuk me-load model YOLO dan SAM 2. Sertakan fungsi `unload_model()` di sini untuk manajemen RAM 8GB Jetson (misal: matikan SAM 2 saat mode Live Counting aktif).
* **`counting_logic.py`**: Murni logika matematika dan *state machine* untuk menentukan kapan counter bertambah, tanpa peduli dari mana gambar berasal.

2. **`app/templates/` & `app/static/` (Presentation)**
* **`templates/`**: File HTML Anda (`.html`). Gunakan sintaks Jinja2 `{{ variable }}` untuk menyisipkan data dari Python.
* **`static/`**: Tempat menyimpan CSS, JS, dan **penting: hasil capture gambar**.
* **`static/captures/`**: Folder ini akan menyimpan hasil foto. Karena berada di dalam folder `static`, Flask otomatis membuatnya bisa diakses via URL (misal: `<img src="/static/captures/session1/img_01.jpg">`) tanpa perlu membuat route API khusus untuk menyajikan gambar.

3. **`weights/`**
Menyimpan file `.pt` (YOLO dan SAM). Pastikan folder ini di-*mount* ke dalam Docker agar kita bisa mengganti model tanpa me-rebuild image.
4. **`run.py`**
Entry point aplikasi. Di sinilah Anda menginisialisasi Flask app dan menjalankan server (bisa menggunakan `app.run(threaded=True)` untuk dev, atau dipanggil via Gunicorn untuk production).

---

### Analisis Spesifikasi & Environment

* **OS:** JetPack 6.x (L4T R36) - Ubuntu 22.04 based.
* **CUDA:** Versi 12.6.
* **Arsitektur:** ARM64 (aarch64).
* **Constraint:** Library Python standar (via `pip install`) seringkali mengunduh versi CPU-only atau x86. Kita **harus** menggunakan Docker Image khusus NVIDIA agar PyTorch bisa mendeteksi GPU.

---

### Strategi Docker (Updated for Flask Monolith)

Kita akan menyederhanakan konfigurasi menjadi **Single Container Service**.

#### 1. `requirements.txt` (Root Folder)

Bersihkan library FastAPI dan ganti dengan Flask. Jangan sertakan `torch/torchvision` karena sudah ada di Base Image.

```text
# --- Web Framework (Flask) ---
Flask>=3.0.0
gunicorn>=21.2.0    # Production server agar video stream stabil
requests>=2.31.0
python-dotenv>=1.0.0

# --- AI & Vision Utils ---
# Install tanpa dependencies agar tidak menimpa torch bawaan image
ultralytics>=8.1.0
opencv-python-headless
Pillow>=10.0.0
numpy>=1.24.0

# --- SAM 2 Dependencies ---
hydra-core>=1.3.2
iopath>=0.1.10
omegaconf>=2.3.0

# --- Hardware Monitor ---
jetson-stats>=4.0.0

```

#### 2. `Dockerfile` (Root Folder)

Kita tetap menggunakan Base Image `dustynv` untuk mendapatkan PyTorch+CUDA yang optimal, namun kita sesuaikan perintah jalannya untuk Flask.

```dockerfile
# Gunakan Base Image JetPack 6 (L4T R36) dengan PyTorch & CUDA pre-installed
FROM dustynv/l4t-pytorch:r36.2.0

# Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

WORKDIR /app

# 1. Install System Dependencies
# libgl1-mesa-glx: dibutuhkan OpenCV
# git: dibutuhkan untuk clone SAM 2
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python Dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 3. Install SAM 2 dari Source (Wajib untuk ARM64/Jetson)
RUN git clone https://github.com/facebookresearch/segment-anything-2.git && \
    cd segment-anything-2 && \
    pip3 install -e .

# 4. Copy Source Code
COPY . .

# 5. Buat folder untuk captures jika belum ada (permission fix)
RUN mkdir -p app/static/captures && chmod -R 777 app/static/captures

# 6. Expose Port Flask Default
EXPOSE 5000

# 7. Command: Jalankan dengan Gunicorn (4 Worker Threads) untuk handle stream & request bersamaan
# Bind ke 0.0.0.0 agar bisa diakses dari luar container
CMD ["gunicorn", "--workers=1", "--threads=4", "--bind", "0.0.0.0:5000", "run:app"]

```

#### 3. `docker-compose.yml` (Root Folder)

Hanya butuh satu service. Sangat bersih.

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: metal_flask_monolith
    runtime: nvidia              # WAJIB: Agar container bisa akses GPU Orin
    network_mode: host           # WAJIB: Agar latency RTSP minimal & akses IP mudah
    privileged: true             # Opsional: Membantu akses hardware kamera USB jika perlu
    environment:
      - FLASK_ENV=production
      - SAM2_CHECKPOINT_PATH=/app/weights/sam2_hiera_tiny.pt
    volumes:
      # Hot-reload: Mount code lokal ke container
      - .:/app
      # Persistence: Pastikan hasil capture tidak hilang saat container restart
      - ./app/static/captures:/app/app/static/captures
      # Mount socket jtop untuk monitoring suhu/GPU dari dalam app
      - /run/jtop.sock:/run/jtop.sock
    restart: unless-stopped

```

### Cara Menjalankan

1. Pastikan struktur folder sudah sesuai.
2. Letakkan file model (`.pt`) di folder `weights/`.
3. Build image:
```bash
docker compose build

```


4. Jalankan aplikasi:
```bash
docker compose up

```


5. Akses Dashboard di browser Jetson atau PC lain di jaringan yang sama: `http://<IP_JETSON>:5000`

### Catatan Kritis: `Flash Attention` pada Jetson

Sama seperti peringatan sebelumnya, **SAM 2** merekomendasikan `flash-attn` untuk kecepatan maksimal. Namun, mengompilasinya di Jetson Orin Nano sering gagal karena kehabisan RAM (OOM) saat compile.

* **Keputusan:** Dockerfile di atas **TIDAK** menginstall `flash-attn`.
* **Dampak:** SAM 2 akan memberikan peringatan (warning) di log console, namun akan otomatis *fallback* ke mode attention standar Math. Ini sedikit lebih lambat tetapi jauh lebih stabil untuk development awal dan deployment cepat. Akurasi tidak terpengaruh.
