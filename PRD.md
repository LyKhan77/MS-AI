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

## 6. Technology Stack & Frameworks
Pemilihan framework ini diprioritaskan untuk **keringanan (lightweight)** pada Jetson Orin Nano namun tetap modern dan responsif.

### A. Backend & AI Engine
* **Language:** Python 3.10+
* **Web Framework (API):** **FastAPI** (Rekomendasi Utama).
    * *Alasan:* Mendukung *Asynchronous* (`async/await`). Ini krusial agar UI tidak *hang* saat AI sedang memproses gambar berat (SAM 2/YOLO).
* **AI Inference:**
    * **Ultralytics YOLO:** Untuk Object Detection & Counting.
    * **SAM 2 (Segment Anything Model 2):** Menggunakan library resmi Meta atau wrapper yang dioptimasi (seperti `mobile-sam` jika VRAM 8GB sangat tertekan).
    * **PyTorch (GPU):** Dengan dukungan CUDA 12.x (JetPack 6).

### B. Frontend Dashboard
* **Framework:** **React.js** atau **Vue.js** (Single Page Application).
    * *Alasan:* Memisahkan beban *rendering* UI dari server Jetson. Browser client (laptop supervisor) yang akan menanggung beban rendering grafis dashboard, sehingga CPU Jetson fokus ke AI.
* **Alternative (Rapid Prototyping):** **Streamlit**.
    * *Catatan:* Jika Anda ingin *development speed* yang sangat cepat tanpa koding HTML/CSS/JS terpisah, gunakan Streamlit. Namun, untuk performa video *real-time* jangka panjang, React/FastAPI lebih stabil.
* **Video Streaming Protocol:** **WebSocket** atau **MJPEG Stream** via OpenCV.
    * *Integrasi:* Menggunakan **MediaMTX** (yang sudah Anda pelajari sebelumnya) untuk me-relay RTSP ke format WebRTC/HLS agar bisa diputar di browser dengan *latency* rendah.

### C. Database & Storage
* **Database:** **SQLite** (via SQLAlchemy atau Tortoise ORM).
    * *Alasan:* Serverless, file-based, sangat ringan, dan cukup untuk menyimpan data sesi dan log produksi harian. Tidak memakan RAM seperti PostgreSQL/MySQL.
* **File Storage:** Local File System (menyimpan capture image & crop defect dalam struktur folder `media/sessions/{date}/{session_id}/`).

### D. Deployment
* **Containerization:** **Docker** & **Docker Compose**.
    * Service 1: Backend API (FastAPI + AI Models).
    * Service 2: Frontend (Nginx/Node).
    * Service 3: Media Server (MediaMTX).

---

## 7. Dashboard Requirements (UI/UX Detail)

Sistem akan memiliki 3 halaman utama yang dapat diakses melalui browser (misal: `http://ip-jetson:3000`).

### 7.1. Halaman 1: Live Monitoring (Operation Mode)
Halaman ini adalah tampilan utama bagi Operator/Mesin saat produksi berjalan.

* **Layout:**
    * **Kiri (Video Feed):** Tampilan Live Camera (RTSP).
        * Overlay Visual: Bounding box pada metal sheet yang terdeteksi.
        * Indikator Status: "Monitoring Active" (Hijau) atau "Paused" (Merah).
    * **Kanan (Control & Stats):**
        * **Session Config:** Input field untuk `Session Name` dan `Max Target Count` (misal: 100 pcs).
        * **Big Counter Panel:** Angka besar menunjukkan jumlah saat ini (misal: **45 / 100**).
        * **Action Buttons:** Tombol besar [START SESSION], [PAUSE], [FINISH SESSION].
        * **Log Feed (Mini):** List teks berjalan: *"14:00:01 - Sheet #45 Detected"*.
* **Logic UI:**
    * Jika `Current Count` > `Max Target`, angka berubah warna jadi Merah + Browser memutar audio alert.
    * Tombol "Defect Check" di-disable saat sesi masih berjalan (untuk mencegah overload VRAM).

### 7.2. Halaman 2: Defect Analysis & Measurement (Post-Process)
Halaman ini digunakan QA/Supervisor setelah sesi selesai untuk memeriksa kualitas.

* **Layout:**
    * **Sidebar:** Daftar Folder Sesi (berdasarkan Tanggal/Nama).
    * **Grid Gallery:** Menampilkan *thumbnail* semua metal sheet yang di-capture pada sesi tersebut.
    * **Detail View (Modal/Popup):**
        * Muncul saat thumbnail diklik.
        * Menampilkan gambar resolusi penuh.
        * **Panel Tool:**
            * Tombol [Auto-Detect Defect]: Memicu YOLO + SAM 2.
            * Tombol [Measure Dimension]: Memicu algoritma pengukuran pixel.
            * Hasil: Menampilkan overlay mask cacat & teks dimensi (Panjang x Lebar mm).
        * **Manual Override:** Checkbox "Reject/Approve" manual oleh user.
* **Output:** Tombol [Generate Report] untuk mengekspor hasil analisis ke PDF/Excel.

### 7.3. Halaman 3: Settings & Calibration
Halaman teknis untuk engineer.

* **Camera:** URL RTSP input, resolusi, FPS limit.
* **Model Config:** Threshold confidence (0.0 - 1.0) untuk YOLO.
* **Calibration:**
    * Input nilai **"Pixel to MM Ratio"**.
    * Fitur "Live Calibration": User menggambar garis pada objek referensi di video, lalu memasukkan panjang aslinya (cm), sistem menghitung rasio otomatis.
* **Alerts:** Upload file suara `.mp3` untuk notifikasi batas maksimum.

---

## 8. Data & API Structure (Draft)

Untuk memudahkan komunikasi Frontend ke Backend, berikut spesifikasi API endpoint kuncinya:

* `POST /api/session/start` -> Payload: `{name: "Batch-A", target: 100}`
* `GET /api/session/status` -> Return: `{count: 45, is_active: true}`
* `POST /api/analyze/defect` -> Payload: `{image_id: "img_001.jpg"}`
    * *Backend Process:* Load Image -> YOLO Inference -> SAM Inference -> Save Crop.
    * *Return:* `{defects: [{type: "scratch", bbox: [...], mask_path: "..."}]}`
* `GET /api/logs/export/{session_id}` -> Return: JSON/CSV file.

---

Berikut adalah struktur direktori proyek yang **modular**, **scalable**, dan siap untuk **Docker**. Struktur ini memisahkan logika AI, API Backend, dan Frontend agar mudah dikelola, terutama saat dideploy di NVIDIA Jetson.

Nama Proyek yang disarankan: `metal-sheet-monitor-ai`

```text
metal-sheet-monitor-ai/
├── 📂 backend/                     # Backend API (FastAPI + AI Engine)
│   ├── 📂 app/                     # Source code utama Python
│   │   ├── 📂 api/                 # Endpoints API (Routes)
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── sessions.py     # API manajemen sesi & counting
│   │   │   │   ├── defects.py      # API trigger analisa defect (SAM 2)
│   │   │   │   ├── streams.py      # API kontrol video/RTSP
│   │   │   │   └── settings.py     # API konfigurasi sistem
│   │   ├── 📂 core/                # Konfigurasi sistem
│   │   │   ├── config.py           # Load .env variables
│   │   │   └── database.py         # Koneksi SQLite
│   │   ├── 📂 models/              # Database Schema (ORM)
│   │   │   └── session_log.py      # Definisi tabel logs
│   │   ├── 📂 schemas/             # Pydantic Models (Validation)
│   │   │   └── payloads.py         # Request/Response format
│   │   ├── 📂 services/            # LOGIKA UTAMA (The "Brain")
│   │   │   ├── 📂 ai/
│   │   │   │   ├── wrapper_yolo.py # Class untuk load/infer YOLO (Counting)
│   │   │   │   ├── wrapper_sam.py  # Class untuk load/infer SAM 2 (Defect)
│   │   │   │   └── utils.py        # Pre/post processing images
│   │   │   ├── camera_manager.py   # Handle RTSP & Video Capture
│   │   │   ├── counting_logic.py   # Algoritma stacking & state machine
│   │   │   └── dimension_calc.py   # Algoritma pengukuran pixel-to-mm
│   │   └── main.py                 # Entry point FastAPI
│   ├── 📂 weights/                 # Tempat menyimpan model AI (.pt)
│   │   ├── yolo_counting.pt        # Model deteksi metal sheet
│   │   ├── yolo_defect.pt          # Model deteksi lokasi cacat
│   │   └── sam2_tiny.pt            # Model segmentasi
│   ├── Dockerfile                  # Konfigurasi build Container Backend
│   └── requirements.txt            # Library Python (torch, ultralytics, fastapi, dll)
│
├── 📂 frontend/                    # Dashboard UI (React/Vue)
│   ├── 📂 public/
│   ├── 📂 src/
│   │   ├── 📂 components/          # Reusable UI (Buttons, Cards)
│   │   ├── 📂 pages/               # Halaman: Monitor, Analysis, Settings
│   │   ├── 📂 services/            # API Client (Axios/Fetch ke Backend)
│   │   └── App.jsx
│   ├── Dockerfile                  # Konfigurasi build Container Frontend
│   └── package.json
│
├── 📂 data/                        # Persisten Data (Volume Docker)
│   ├── 📂 db/                      # Tempat file SQLite disimpan
│   │   └── production.db
│   └── 📂 media/                   # Penyimpanan gambar hasil capture
│       └── 📂 sessions/
│           ├── 📂 batch_20241217_A/
│           │   ├── raw_001.jpg
│           │   ├── defect_crop_001.png
│           │   └── ...
│
├── .env                            # Environment Variables (JANGAN DI-PUSH KE GIT)
├── .gitignore
├── docker-compose.yml              # Orkestrasi container (Backend + Frontend)
└── README.md                       # Dokumentasi cara install & run
```

### Penjelasan Folder Kunci untuk Developer

1.  **`backend/app/services/` (Paling Penting)**
    Di sinilah "otak" sistem Anda berada. Pisahkan logika AI dari logika API.

      * `counting_logic.py`: Berisi *State Machine* (State 0: Empty, State 1: Motion, State 2: Object). Ini memastikan counting tidak *double count*.
      * `ai/wrapper_sam.py`: Buat fungsi untuk *load* dan *unload* model SAM. Karena SAM berat, Anda mungkin perlu fungsi `unload_model()` untuk membebaskan VRAM saat sedang mode *Live Counting* (YOLO), dan me-load ulang saat user masuk menu *Defect Analysis*.

2.  **`backend/weights/`**
    Folder khusus untuk menyimpan file `.pt`. Pastikan folder ini masuk `.gitignore` jika ukurannya besar, tapi di dalam Docker, folder ini akan di-*copy* atau di-*mount*.

3.  **`data/` (Volume Mapping)**
    Saat menggunakan Docker di Jetson, data di dalam container akan hilang jika container di-restart. Oleh karena itu, folder `data/` di host (Jetson) akan di-*mount* ke dalam container agar database dan gambar hasil capture aman.

4.  **`frontend/`**
    Terpisah sepenuhnya. Ini memungkinkan Anda untuk mengembangkan UI di laptop (Windows/Mac) tanpa perlu konek ke Jetson terus-menerus, cukup arahkan API URL-nya ke IP Jetson.


**Analisis Spesifikasi Anda:**

  * **OS:** JetPack 6.x (L4T R36.4.7) - Ini adalah versi terbaru berbasis **Ubuntu 22.04**.
  * **CUDA:** Versi **12.6** (Sangat baru).
  * **PyTorch Host:** Anda sudah memiliki `torch 2.8.0` di host. Ini versi yang sangat baru dan mungkin hasil build khusus (nightly/custom), karena versi stabil standar untuk Jetson biasanya sedikit di bawah itu.
  * **GPU:** Orin Nano (Ampere Architecture).

### Strategi Docker untuk Anda

Kita **tidak bisa** menggunakan `requirements.txt` standar PC. Jika kita membiarkan `pip` menginstall `torch` dari internet di dalam Docker, ia akan mendownload versi PC (x86) atau versi ARM generic yang **tidak memiliki akselerasi GPU (CUDA)**.

Kita akan menggunakan **Base Image** dari `dustynv` (NVIDIA Developer) yang spesifik untuk **JetPack 6 (R36)**. Base image ini sudah berisi PyTorch dan CUDA yang teroptimasi.

Berikut adalah file-file konfigurasi yang harus Anda buat di dalam folder `backend/`:

-----

### 1\. `backend/requirements.txt`

**PENTING:** Perhatikan bahwa `torch`, `torchvision`, dan `tensorrt` **TIDAK** dicantumkan di sini. Mereka akan disediakan oleh Base Image.

```text
# --- AI & Vision Utils ---
# Ultralytics (YOLO)
# Kita install tanpa deps agar tidak menimpa torch bawaan image
ultralytics>=8.1.0
# OpenCV Headless (agar tidak butuh GUI X11 di server)
opencv-python-headless
# Image processing
Pillow>=10.0.0
numpy>=1.24.0
matplotlib>=3.7.0

# --- SAM 2 Dependencies ---
# SAM 2 butuh library ini
hydra-core>=1.3.2
iopath>=0.1.10
omegaconf>=2.3.0

# --- Backend API ---
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.7
pydantic>=2.6.0
pydantic-settings>=2.2.0
requests>=2.31.0

# --- Database & System ---
SQLAlchemy>=2.0.25
aiosqlite>=0.19.0
python-dotenv>=1.0.0
jetson-stats>=4.0.0
```

-----

### 2\. `backend/Dockerfile`

Dockerfile ini dirancang khusus untuk Jetson Orin Nano dengan JetPack 6. Ia akan menginstall SAM 2 secara manual dari source code karena belum ada wheel resminya untuk ARM64.

```dockerfile
# Gunakan Base Image JetPack 6 (L4T R36) yang sudah ada PyTorch & CUDA
# Tag r36.2.0 cukup stabil untuk R36.4 user
FROM dustynv/l4t-pytorch:r36.2.0

# Set environment variables agar Python output langsung muncul di log (unbuffered)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# 1. Install System Dependencies (Linux level)
# libgl1-mesa-glx dibutuhkan oleh OpenCV
# git dibutuhkan untuk clone SAM 2
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip (Opsional tapi disarankan)
RUN pip3 install --upgrade pip

# 3. Copy dan Install Python Requirements
COPY requirements.txt .
# --no-deps pada ultralytics untuk mencegah overwrite torch
RUN pip3 install -r requirements.txt

# 4. Install SAM 2 (Segment Anything Model 2) dari Source
# Karena kita di Jetson, compile manual lebih aman
RUN git clone https://github.com/facebookresearch/segment-anything-2.git && \
    cd segment-anything-2 && \
    pip3 install -e .

# 5. Copy seluruh source code aplikasi
COPY . .

# 6. Expose port FastAPI
EXPOSE 8000

# 7. Perintah default saat container jalan
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

-----

### 3\. `docker-compose.yml` (Di Root Project)

Gunakan konfigurasi ini untuk memastikan container bisa mengakses GPU Orin Nano.

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: metal_ai_backend
    # Runtime NVIDIA wajib untuk Jetson
    runtime: nvidia
    network_mode: host # Rekomendasi untuk RTSP stream latency rendah
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
      # Agar SAM 2 menggunakan checkpoint yang benar
      - SAM2_CHECKPOINT_PATH=/app/weights/sam2_hiera_tiny.pt
    volumes:
      # Mapping folder host ke container
      - ./backend:/app
      - ./data:/app/data
      # Mount socket jtop agar bisa baca stats dari dalam container
      - /run/jtop.sock:/run/jtop.sock
    restart: unless-stopped

  # Frontend nanti ditambahkan di sini
  # frontend: ...
```

### Cara Build & Run

1.  Buat folder dan file sesuai struktur di atas.
2.  Masuk ke terminal di root folder `metal-sheet-monitor-ai`.
3.  Jalankan perintah build:
    ```bash
    sudo docker compose build
    ```
    *(Proses ini akan memakan waktu 15-30 menit karena harus mendownload base image yang besar (\~8GB) dan mungkin melakukan compile ringan).*
4.  Jalankan container:
    ```bash
    sudo docker compose up
    ```

### Catatan Kritis untuk SAM 2 di Jetson

SAM 2 biasanya merekomendasikan instalasi `flash-attn` (Flash Attention) untuk performa maksimal.

  * **Isu:** Mengcompile `flash-attn` di Jetson Orin Nano bisa memakan waktu **2-4 jam** dan sering gagal jika RAM habis (OOM).
  * **Solusi:** Di Dockerfile di atas, saya **TIDAK** menyertakan instalasi `flash-attn`. SAM 2 tetap bisa berjalan tanpa itu (fallback ke attention standar Math), hanya sedikit lebih lambat. Untuk tahap awal (Development), ini jauh lebih aman.
