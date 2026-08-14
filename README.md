# ⚡ OCH-Subagent (Optical Character & Document Intelligence Multi-Agent System)

Sistem pemrosesan dokumen PDF dan struk belanja (PNG/JPG) berbasis multi-agent dengan antarmuka interaktif 3-panel (**PDF/Image Viewer**, **Hasil OCR & JSON Inspector**, **Subagent Chat**) yang dilengkapi dengan **7 Lapisan Pengaman Kuota Bersama (7-Person Shared Safety & Anti-429 Rate Limiter)**.

---

## 🌟 Fitur Utama

- 📑 **Interactive Document Viewer**: Visualisasi per halaman PDF dan file gambar struk (PNG/JPG/WEBP) dengan kontrol navigasi `◀ / ▶` dan zoom.
- ⚡ **Ekstraksi OCR Cepat**: Integrasi model `ocr-lighton` dengan format payload Base64 array.
- 🧩 **Structuring & Schema Inspector**: Subagent parser `qwen-35b` yang otomatis menata data dokumen/pemerintah dan struk belanja (merchant, rincian barang, subtotal, diskon, PPN, total bayar).
- 💬 **Interactive Subagent Chat**: Chatbot cerdas grounded langsung pada teks OCR dokumen menggunakan model `qwen-35b` atau `nemotron-35`.
- 🛡️ **7-Person Shared-Team Safety Shield**:
  - **Local SHA-256 Hash Cache**: Pengujian berulang pada gambar/dokumen yang sama = **0 Token Cost / 0 API Calls**.
  - **Anti-Spam Rate Limiter**: Jeda minimum 30 detik untuk OCR + lock konkurensi = 1 agar tidak memonopoli kuota server.
  - **Jittered 429 Backoff**: Penanganan tabrakan otomatis jika menerima HTTP 429 dari server.
  - **Top Safety Bar**: Status cooldown real-time detik per detik di bagian atas aplikasi.
- 📥 **Hugging Face Dataset Integration**: Download sample dataset langsung dari [BEE-spoke-data/govdocs1-pdf-source](https://huggingface.co/datasets/BEE-spoke-data/govdocs1-pdf-source).

---

## 🏗️ Struktur Proyek

```
OCH-Subagent/
├── .env.example              # Template konfigurasi environment (tanpa API key rahasia)
├── .gitignore                # Pengecualian file sensitif (.env, cache, sqlite)
├── requirements.txt          # Dependensi Python
├── main.py                   # Entrypoint aplikasi server & web
├── plan.md                   # Blueprint teknis arsitektur
├── data/
│   └── govdocs/              # Direktori penyimpanan PDF & struk gambar
├── src/
│   ├── config.py             # Pydantic settings & konfigurasi sistem
│   ├── dataset/
│   │   ├── hf_downloader.py  # Downloader dataset dari Hugging Face
│   │   └── init_samples.py   # Inisialisasi data sampel awal
│   ├── limiter/
│   │   ├── rate_limiter.py   # Jeda 30s & Concurrency lock
│   │   └── quota_guard.py    # Pelacak kuota lokal & daily hard-cap
│   ├── client/
│   │   ├── base_client.py    # Client HTTP + 429 Jitter Backoff + Mock Mode
│   │   └── ocr_client.py     # Base64 encoder untuk ocr-lighton
│   ├── cache/
│   │   └── local_cache.py    # SQLite SHA-256 hash cache
│   ├── agents/
│   │   ├── base_agent.py     # Base abstract class subagent
│   │   ├── ocr_agent.py      # Subagent ekstraksi OCR (ocr-lighton)
│   │   ├── parser_agent.py   # Subagent parsing JSON terstruktur
│   │   └── chat_agent.py     # Subagent tanya-jawab interaktif
│   ├── pipeline/
│   │   ├── orchestrator.py   # Multi-agent coordinator
│   │   └── schemas.py        # Pydantic schemas (Dokumen & Struk Belanja)
│   ├── server/
│   │   └── app.py            # FastAPI REST backend & Static Web server
│   └── utils/
│       ├── image_utils.py    # Image optimizer & Base64 URI builder
│       └── pdf_utils.py      # PyMuPDF page-to-image rasterizer
├── web/
│   ├── index.html            # Dashboard UI 3-Panel
│   ├── style.css             # Glassmorphic dark mode styling
│   └── app.js                # Frontend controller & live polling
└── tests/
    ├── test_cache.py         # Unit test cache SHA-256
    ├── test_limiter.py       # Unit test rate limiter
    ├── test_mock_pipeline.py # Unit test end-to-end pipeline
    └── test_live_api.py      # Live connectivity diagnostic test
```

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Kloning Repositori
```bash
git clone https://github.com/loxleyftsck/OCH-Subagent.git
cd OCH-Subagent
```

### 2. Buat Virtual Environment & Pasang Dependensi
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# atau
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Konfigurasi Environment
Salin template konfigurasi:
```bash
cp .env.example .env
```
Sesuaikan `API_BASE_URL` dan `API_KEY` di dalam file `.env`:
```ini
API_BASE_URL=http://10.7.1.21/v1
API_KEY=sk-your_api_key_here
```

### 4. Jalankan Aplikasi
```bash
python main.py
```
Buka browser di:
👉 **`http://localhost:8000`**
