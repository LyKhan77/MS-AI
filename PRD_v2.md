Tentu, ini adalah **Product Requirement Document (PRD) v1.2** yang sangat detail, disesuaikan dengan workflow **Manual Station**, hardware **Jetson Orin Nano**, dan framework **Streamlit**.

Dokumen ini ditulis dengan standar teknis tinggi agar siap digunakan sebagai acuan pengembangan software oleh Anda sebagai AI Programmer.

-----

# Product Requirement Document (PRD)

**Project Name:** Metal Sheet AI Inspection System (MS-AIS)
**Version:** 1.2 (Final Detailed)
**Date:** 16 December 2025
**Owner:** AI Dept - PT GSPE
**Target Hardware:** NVIDIA Jetson Orin Nano (8GB RAM Recommended)
**Software Stack:** Python 3.10, Streamlit, PyTorch, OpenCV, TensorRT

-----

## 1\. Executive Summary

Mengembangkan sistem *Quality Control* (QC) berbasis *Computer Vision* untuk stasiun kerja manual. Sistem ini bertujuan membantu operator dalam memverifikasi dimensi dan mendeteksi cacat permukaan (*scratch, dent*) pada lembaran logam (*metal sheet*) secara *non-contact*.

Sistem menggunakan **Streamlit** sebagai antarmuka pengguna (HMI) karena kecepatan pengembangan, dan model AI berbasis **SAM (Segment Anything Model)** yang dioptimasi untuk edge device guna melakukan segmentasi presisi tinggi. Input sistem fleksibel antara kamera langsung (RTSP/USB) atau file video untuk keperluan validasi/testing.

-----

## 2\. Problem Statement & Goals

### 2.1. Masalah Saat Ini

  * Pengukuran manual menggunakan mistar/caliper memakan waktu dan rawan *human error*.
  * Pemeriksaan cacat permukaan bersifat subjektif tergantung kelelahan mata operator.
  * Tidak ada bukti digital (log gambar) untuk produk yang di-reject.

### 2.2. Tujuan (Goals)

  * **Otomasi:** Mengukur dimensi Panjang (L) & Lebar (W) secara otomatis dalam \< 3 detik setelah barang diletakkan.
  * **Akurasi:** Toleransi kesalahan pengukuran dimensi \< 2mm.
  * **Fleksibilitas:** Mendukung input RTSP (Produksi) dan Video Upload (R\&D/Testing).
  * **Cost-Effective:** Berjalan lancar di *Edge Device* (Jetson Orin Nano) tanpa server GPU mahal.

-----

## 3\. User Personas & User Stories

### 3.1. Operator Produksi (End User)

> *"Sebagai operator, saya ingin meletakkan barang di meja dan langsung melihat lampu hijau/merah di layar tanpa harus menekan tombol mouse/keyboard setiap kali, agar tangan saya fokus memindahkan barang."*

### 3.2. AI Engineer (Admin)

> *"Sebagai engineer, saya ingin bisa mengupload video rekaman cacat ke sistem untuk menyetel sensitivitas (threshold) deteksi tanpa harus berada di lini produksi, dan memilih input RTSP saat sistem siap live."*

-----

## 4\. Functional Requirements (FR)

### 4.1. Module: Input Source Management

  * **FR-01 (Source Selection):** UI Sidebar harus memiliki **Radio Button** dengan opsi:
    1.  `Live Camera (RTSP/USB)`
    2.  `Video File (Upload)`
  * **FR-02 (RTSP Handler):**
      * Input field: `RTSP URL` (String). Default: `0` (Local Webcam).
      * Error Handling: Auto-reconnect jika stream terputus selama \< 5 detik. Tampilkan pesan "Camera Disconnected" jika timeout.
  * **FR-03 (File Handler):**
      * Widget: `st.file_uploader` (Format: mp4, avi, mov).
      * Behavior: Video diputar *looping* otomatis saat mode monitoring aktif.

### 4.2. Module: Pre-Processing (Smart Trigger)

  * **FR-04 (Region of Interest - ROI):** Sistem memungkinkan *cropping* area meja kerja untuk membuang background lantai yang tidak perlu.
  * **FR-05 (Stability Check/Motion Filter):**
      * Sistem tidak boleh melakukan inferensi AI berat saat tangan operator masih bergerak.
      * **Logic:** Gunakan *Frame Difference* sederhana. Jika perubahan piksel \< 5% selama 1 detik -\> Trigger AI Process.

### 4.3. Module: AI Core (SAM3 & CV)

  * **FR-06 (Segmentation):**
      * Model: **MobileSAM** atau **FastSAM** (Turunan SAM yang dikonversi ke TensorRT `.trt` atau `.engine`). *Jangan gunakan SAM-Huge original karena latensi tinggi.*
      * Output: Binary Mask (0=Background, 1=Metal Sheet).
  * **FR-07 (Dimension Measurement):**
      * Logic: `cv2.minAreaRect` pada Mask untuk mendapatkan bounding box rotasi (antisipasi operator menaruh miring).
      * Calibration: Input field di Sidebar `Pixel-to-MM Ratio` (Float).
  * **FR-08 (Surface Defect Detection):**
      * Logic (Phase 1): Melakukan analisis histogram/tekstur pada area di dalam Mask (Masked Image). Area dengan kontras tinggi mendadak ditandai sebagai `Potential Defect`.
      * Logic (Phase 2): Klasifikasi AI (Custom Trained) jika dataset sudah terkumpul.

### 4.4. Module: Dashboard & Feedback (Streamlit)

  * **FR-09 (Layout):**
      * **Sidebar:** Konfigurasi (Source, Threshold, Calibration, Start/Stop).
      * **Main Area:** Video Player (Besar), Kartu Status (OK/NG), Statistik Dimensi.
  * **FR-10 (Visual Feedback):**
      * Overlay Masking: Warna Hijau transparan jika OK, Merah transparan jika NG.
      * Text Overlay: Dimensi ditampilkan di dekat objek.
  * **FR-11 (Auditory Feedback):**
      * Memainkan suara `.wav` pendek saat status berubah dari "Processing" menjadi "OK" atau "NG".
      * *Note:* Karena keterbatasan browser, audio mungkin memerlukan interaksi user pertama kali (Auto-play policy).

-----

## 5\. Non-Functional Requirements (NFR)

  * **NFR-01 (Latency):** Total waktu dari benda diam hingga hasil keluar maksimal **2 detik**.
  * **NFR-02 (Display FPS):** Video stream di UI minimal **15 FPS** agar tidak terlihat patah-patah, meskipun inferensi AI berjalan di background (asynchronous).
  * **NFR-03 (Resource Usage):** Penggunaan RAM \< 6GB (menyisakan 2GB untuk OS Jetson).
  * **NFR-04 (Thermal):** Aplikasi tidak boleh menyebabkan Jetson *throttling* (suhu \> 80°C) dalam pemakaian normal (gunakan mode daya `15W` atau `MAXN` dengan kipas aktif).

-----

## 6\. Technical Architecture & Data Flow

### 6.1. High Level Diagram

```mermaid
[Camera/File] --> [OpenCV Decoder] --> [Motion Detector] --> [Trigger Gate]
                                              | (No Motion)
                                              v
[Streamlit UI] <---- [Visual Overlay] <--- [AI Inference (SAM + CV)]
```

### 6.2. Stack Detail

1.  **Backend Logic:** Python 3.8+
2.  **Web Framework:** Streamlit (dengan `streamlit-webrtc` jika nanti butuh performa lebih tinggi, tapi `st.image` cukup untuk PoC).
3.  **Computer Vision:** OpenCV (`cv2`) dengan CUDA support (jika memungkinkan build OpenCV with CUDA di Jetson).
4.  **AI Model:** `Ultralytics` (untuk FastSAM/YOLO-World) atau `mobile_sam` library.

-----

## 7\. Detailed UI/UX Specifications

### Sidebar Menu Structure

1.  **Mode Selector:** `[Radio] Input Source`
2.  **Connection:** `[Input] RTSP URL / Camera ID`
3.  **Calibration:** `[Slider] Scale (px/mm)`
4.  **Detection Sensitivity:**
      * `[Slider] Confidence Threshold (0.0 - 1.0)`
      * `[Slider] Defect Sensitivity (Area Size)`
5.  **Actions:**
      * `[Button Primary] ▶ START Monitoring`
      * `[Button Secondary] ⏹ STOP`
      * `[Checkbox] Save NG Images`

### Main Dashboard Layout

  * **Header:** Logo Perusahaan & Status Sistem (Idle/Scanning/Result).
  * **Row 1 (Video):** `st.image` placeholder yang di-update via loop. Resolusi display disarankan 640x480 untuk meringankan bandwidth browser, namun processing tetap di HD.
  * **Row 2 (Result Cards):** 3 Kolom
      * *Col 1:* **STATUS** (Besar, Text Hijau/Merah).
      * *Col 2:* **Length** (mm).
      * *Col 3:* **Width** (mm).

-----

## 8\. Development Roadmap (Timeline)

### Week 1: Core Foundation (Current Phase)

  * [x] Setup Project Structure.
  * [ ] Implementasi Streamlit UI dasar dengan Radio Button Input.
  * [ ] Implementasi `VideoHandler` class yang bisa switch antara File dan Webcam.
  * [ ] Integrasi algoritma "Static Trigger" (deteksi benda diam).

### Week 2: AI Implementation (SAM Integration)

  * [ ] Install & Test `MobileSAM` di Jetson Orin.
  * [ ] Buat modul `DimensionCalculator` (Pixel to MM logic).
  * [ ] Integrasi output SAM Mask ke Video Overlay Streamlit.

### Week 3: Defect Logic & Optimization

  * [ ] Implementasi logika deteksi cacat pada area Mask.
  * [ ] Integrasi Alert System (UI Notification).
  * [ ] Fitur Auto-Save gambar NG ke folder lokal.

### Week 4: UAT & Tuning

  * [ ] Kalibrasi akurasi dimensi dengan penggaris fisik.
  * [ ] Stress test (Running 4 jam nonstop).
  * [ ] Serah terima ke user (Operator).

-----

## 9\. Appendix: Project Folder Structure (Updated)

```text
ms_aims_streamlit/
│
├── .streamlit/
│   └── config.toml         # [server] headless = true, runOnSave = false
│
├── data/
│   ├── inputs/             # Tempat taruh video sample untuk testing
│   ├── outputs_ng/         # Auto-save gambar NG
│   └── outputs_ok/         # Auto-save gambar OK (opsional)
│
├── models/
│   └── mobile_sam.pt       # Bobot model AI
│
├── src/
│   ├── __init__.py
│   ├── camera.py           # Class: VideoStreamer (Threaded)
│   ├── detector.py         # Class: AI_Engine (Load Model, Inference)
│   ├── processing.py       # Utils: Motion Detection, Pix2MM, Overlay
│   └── ui_components.py    # Reusable UI widgets
│
├── app.py                  # Main Application
├── requirements.txt        # streamlit, opencv-python, ultralytics, supervision
└── README.md
```

Dokumen ini sekarang siap digunakan sebagai "Kitab Suci" pengembangan proyek ini. Anda bisa langsung mulai coding modul per modul sesuai struktur di atas.