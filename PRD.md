Berikut adalah **Product Requirement Document (PRD) Final (Versi 1.0)** untuk sistem **Metal Sheet AI Monitor**.

---

# Product Requirement Document (PRD)
**Project Name:** Metal Sheet AI Monitor (MS-AIM)
**Version:** 1.0
**Date:** 16 December 2025
**Platform:** NVIDIA Jetson Orin Nano
**Framework:** NiceGUI (Python)
**AI Engine:** SAM3 (Optimized/Mobile Variant) + OpenCV

## 1. Executive Summary
Mengembangkan sistem *monitoring* dan *quality control* (QC) berbasis visi komputer untuk stasiun kerja manual lembaran logam. Sistem ini bertujuan untuk mengotomatisasi pengukuran dimensi dan deteksi cacat permukaan secara *contactless* saat operator meletakkan lembaran di meja kerja, memberikan umpan balik instan (Visual & Audio) untuk meningkatkan efisiensi dan mengurangi *human error*.

## 2. System Workflow (Manual Station)
Sistem dirancang untuk siklus kerja manual dengan alur sebagai berikut:
1.  **Idle:** Kamera memonitor meja kerja yang kosong.
2.  **Placement:** Operator meletakkan lembaran logam.
3.  **Trigger:** Sistem mendeteksi keberadaan objek (Motion/Object Trigger) dan menstabilkan *capture*.
4.  **Processing:**
    * AI melakukan segmentasi (SAM3).
    * CV menghitung dimensi (Px to mm).
    * CV menganalisis anomali permukaan (Defect).
5.  **Feedback:** Dashboard menampilkan hasil, bunyi alarm jika NG (No-Go).
6.  **Removal:** Operator mengangkat lembaran, sistem reset ke status Idle.

## 3. Functional Requirements

### 3.1. Data Acquisition & Triggering
* **REQ-01 (Camera Input):** Sistem harus mendukung input kamera resolusi tinggi (Min. 1080p, disarankan 4K) dengan posisi *top-down* (tegak lurus).
* **REQ-02 (Smart Trigger):** Sistem harus otomatis membedakan antara "tangan operator sedang bekerja" dan "lembaran sudah diletakkan diam" (Delay capture ~1-2 detik setelah gerakan berhenti) untuk menghindari foto tangan operator.

### 3.2. AI & Image Processing (Core)
* **REQ-03 (Segmentation):** Menggunakan model turunan SAM (Segment Anything Model) yang dioptimasi untuk Edge (contoh: NanoSAM / MobileSAM) untuk memisahkan metal sheet dari background meja.
* **REQ-04 (Dimensioning):**
    * Sistem harus mampu mengukur Panjang dan Lebar lembaran.
    * Menyediakan fitur **Kalibrasi Referensi** (menggunakan objek kalibrasi fisik) untuk konversi piksel ke milimeter.
* **REQ-05 (Defect Detection):**
    * Mendeteksi anomali tekstur di dalam area segmentasi (Goresan, Penyok, Lubang).
    * *Initial Strategy:* Computer Vision Thresholding & Edge Detection pada area *masked*.
    * *Future Strategy:* AI Classification (setelah dataset terkumpul).

### 3.3. User Interface (NiceGUI Dashboard)
* **REQ-06 (Live Feed):** Menampilkan video stream MJPEG real-time.
* **REQ-07 (Result Overlay):**
    * *Bounding Box* warna Hijau (OK) atau Merah (NG).
    * Teks Dimensi (misal: "300x200 mm") ditampilkan di atas objek.
* **REQ-08 (Notifications):**
    * **Visual:** Toast notification "PASS" (Hijau) atau "REJECT: Scratch Detected" (Merah).
    * **Audio:** Sound effect berbeda untuk OK (misal: *ding*) dan NG (misal: *buzzer/beep*).
* **REQ-09 (Settings Panel):** Halaman konfigurasi untuk menyetel *Threshold Defect* (sensitivitas) dan melakukan *Kalibrasi Kamera*.

### 3.4. Data Management
* **REQ-10 (Auto-Logging):** Menyimpan log hasil inspeksi (Timestamp, Dimensi, Status OK/NG) ke file CSV/Database lokal.
* **REQ-11 (Image Evidence):** Menyimpan gambar hasil inspeksi (hanya gambar yang NG atau sampel 10% OK) ke penyimpanan lokal.
* **REQ-12 (Storage Maintenance):** Skrip otomatis untuk menghapus data gambar terlama jika penyimpanan Jetson > 80% penuh.

## 4. Non-Functional Requirements
* **NFR-01 (Latency):** Total waktu proses (dari *capture* hingga *alert*) maksimal 3 detik.
* **NFR-02 (Resource Efficiency):** Penggunaan RAM tidak boleh melebihi kapasitas fisik Jetson Orin Nano (hindari Swapping berlebihan).
* **NFR-03 (Stability):** UI Dashboard tidak boleh *freeze* saat AI sedang memproses berat (menggunakan *async/threading*).
* **NFR-04 (UX):** Dashboard harus dapat diakses via browser dari Laptop/Tablet di jaringan lokal (Remote UI), bukan dijalankan langsung di desktop Jetson (Headless Mode disarankan).

## 5. Technical Specifications
| Komponen | Spesifikasi |
| :--- | :--- |
| **Hardware** | NVIDIA Jetson Orin Nano (4GB/8GB RAM) |
| **Camera** | USB Webcam / CSI Camera (Wide Angle, Low Distortion) |
| **OS** | Ubuntu 20.04 (JetPack 5.x/6.x) |
| **Language** | Python 3.8+ |
| **Backend AI** | PyTorch (GPU Enabled), Ultralytics (opsional), OpenCV (CUDA enabled preferred) |
| **Frontend** | NiceGUI |
| **Optimization** | TensorRT (wajib untuk model SAM) |

## 6. Implementation Roadmap

### Phase 1: Foundation (Minggu 1)
* Setup Jetson Orin Nano & Environment (PyTorch, CUDA).
* Install NiceGUI & Setup Camera Stream.
* Implementasi logika "Static Trigger" (Background Subtraction sederhana).

### Phase 2: Dimension & Segmentation (Minggu 2)
* Integrasi model SAM (versi ringan/Mobile) untuk mendapatkan Mask.
* Implementasi fitur Kalibrasi & Pengukuran Dimensi.
* Test akurasi pengukuran fisik.

### Phase 3: Defect Detection & Data Collection (Minggu 3)
* Implementasi algoritma deteksi anomali berbasis CV (Blob/Edge detection).
* Fitur "Save Image" untuk mengumpulkan dataset cacat nyata.
* Integrasi notifikasi suara & toast di NiceGUI.

### Phase 4: Optimization & Deployment (Minggu 4)
* Konversi Model ke TensorRT untuk kecepatan.
* Stress test (menjalankan sistem berjam-jam).
* Final deployment di area produksi.

---
