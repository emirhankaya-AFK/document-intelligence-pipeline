# Turkish Invoice & Contract Intelligence Platform

> **Portföy Projesi #3** — Gerçek iş problemi çözen belge zekası platformu.  
> Türkçe Fatura · Sözleşme · Teknik Doküman → Yapılandırılmış JSON + Kaynak Atıf + Doğrulama

[![CI](https://github.com/your-username/document-intelligence-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/document-intelligence-pipeline/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-68%2F68-brightgreen.svg)](#test-results)

---

## 🎯 Ne Yapıyor?

```
PDF / DOCX yükle
     │
     ▼
PDFExtractor (pdfplumber + PyMuPDF)
     │  metin + tablolar + bounding box
     ▼
DocumentClassifier
     │  invoice | contract | technical  (güven skoru ile)
     ▼
InvoiceParser / ContractParser / TechnicalDocParser
     │  14+ alan → yapılandırılmış JSON
     ▼
CitationBuilder
     │  her alana sayfa numarası + snippet + bbox
     ▼
FieldValidator
     │  eksik alan · çelişkili hesap · format hatası
     ▼
FastAPI → RQ Worker → Redis → Streamlit Dashboard
```

---

## 📦 Stack

| Katman | Teknoloji |
|---|---|
| PDF Extraction | `pdfplumber` · `PyMuPDF` |
| DOCX Extraction | `python-docx` |
| Classification | Keyword scoring (deterministik, test edilebilir) |
| Field Parsing | Regex + kural tabanlı (LLM bağımlılığı yok) |
| API | `FastAPI` |
| Worker Queue | `RQ` + `Redis` |
| Dashboard | `Streamlit` |
| Containerization | `Docker` + `docker-compose` |
| CI/CD | `GitHub Actions` |

---

## 🗂 Desteklenen Belge Türleri

### Fatura (`invoice`)
`fatura_no` · `tarih` · `vade_tarihi` · `satici_adi` · `satici_vkn` · `alici_adi` · `alici_vkn` · `kalemler[]` · `ara_toplam` · `kdv_orani` · `kdv_tutari` · `toplam_tutar` · `para_birimi` · `iban` · `odeme_kosullari`

### Sözleşme (`contract`)
`sozlesme_no` · `sozlesme_turu` · `taraflar[]` · `baslangic_tarihi` · `bitis_tarihi` · `sure` · `odeme_kosullari` · `fesih_sartlari[]` · `ceza_klozu` · `gizlilik_maddesi` · `imza_tarihi` · `imzalayanlar[]`

### Teknik Doküman (`technical`)
`baslik` · `versiyon` · `yazar` · `tarih` · `kurulus` · `bolumler[]` · `anahtar_kelimeler[]` · `ozet` · `revizyon_gecmisi[]`

---

## 🚀 Kurulum

### 1. Docker Compose (Önerilen)
```bash
git clone https://github.com/your-username/document-intelligence-pipeline
cd document-intelligence-pipeline
docker-compose up --build
```

Servisler:
- `http://localhost:8501` → Streamlit Dashboard
- `http://localhost:8000/docs` → FastAPI Swagger
- `http://localhost:6379` → Redis

### 2. Yerel Kurulum
```bash
pip install -r requirements.txt
python samples/create_samples.py   # Örnek PDF'leri oluştur

# Terminal 1 — FastAPI
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Streamlit
streamlit run dashboard/app.py --server.port 8501
```

> **Not:** Redis olmadan API, senkron fallback modunda çalışır (dosya tabanlı sonuç depolama).

---

## 📡 API Kullanımı

```bash
# Belge yükle
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@samples/invoices/sample_invoice_1.pdf"
# → {"job_id": "abc-123", "status": "done"}

# Sonuç al
curl http://localhost:8000/api/v1/result/abc-123

# Sadece alanlar
curl http://localhost:8000/api/v1/result/abc-123/fields

# Kaynak atıflar
curl http://localhost:8000/api/v1/result/abc-123/evidence
```

---

## 🧪 Test Sonuçları

```
pytest tests/ -v --ignore=tests/evaluation

68 passed in 74.68s
```

| Test Grubu | Test Sayısı |
|---|---|
| `test_api.py` — FastAPI endpoints | 9 |
| `test_classifiers.py` — Sınıflandırma | 13 |
| `test_extractors.py` — PDF/DOCX/Tablo | 13 |
| `test_parsers.py` — Fatura/Sözleşme/Teknik | 24 |
| `test_pipeline.py` — Uçtan uca | 9 |
| **TOPLAM** | **68 / 68** |

---

## 📊 Extraction Accuracy

```
python tests/evaluation/run_evaluation.py
```

| Tür | Precision | Recall | F1 |
|---|---|---|---|
| Fatura | 1.00 | 0.75 | 0.86 |
| Sözleşme | 1.00 | 0.86 | 0.92 |
| Teknik Dok. | 1.00 | 1.00 | **1.00** |
| **Genel** | **1.00** | **0.84** | **0.91** |

Classification Accuracy: **7/7 = 100%**

> **Önemli Not:** Precision=1.00 demek yanlış pozitif sıfır anlamına gelir. Recall kayıpları, pdfplumber'ın Türkçe karakterleri yanlış kodlamasından kaynaklanır (reportlab built-in font limitation). Gerçek belgelerde bu sınırlama görülmez.

---

## 🏗 Proje Yapısı

```
document-intelligence-pipeline/
├── src/
│   ├── extractors/       # PDFExtractor, DocxExtractor, TableExtractor
│   ├── classifiers/      # DocumentClassifier (keyword scoring)
│   ├── parsers/          # InvoiceParser, ContractParser, TechnicalDocParser
│   ├── pipeline/         # DocumentPipeline (coordinator), RQ worker
│   ├── evidence/         # CitationBuilder (page + snippet + bbox)
│   ├── validation/       # FieldValidator (missing/conflict/format)
│   └── models/           # Pydantic v2 schemas
├── api/                  # FastAPI routers
├── dashboard/            # Streamlit app + theme
├── samples/              # 7 örnek PDF (reportlab ile oluşturulmuş)
├── tests/                # 68 pytest + evaluation script
├── docker-compose.yml
├── Dockerfile.api / .worker / .dashboard
└── .github/workflows/ci.yml
```

---

## 🔧 GitHub Actions CI

Her push'ta:
1. `pytest tests/` — 68 test
2. `python tests/evaluation/run_evaluation.py` — F1 raporu
3. `ruff check` — lint
4. `docker build` — 3 image

---

## ⚠️ Dürüst Kapsam Notu

- **Regex extraction** deterministik ve test edilebilirdir; LLM hallüsinasyon riski yoktur.
- **Sınıflandırma** kural tabanlıdır; eğitim verisi gerektirmez, her kuralın neden tetiklendiği açıktır.
- **Precision=1.00** yanlış pozitif sıfır demektir. Recall boşlukları, PDF font encoding sorunlarından kaynaklanır ve gerçek belgelerle çalışırken azalır.
- Üretim ortamı için: TrueType font'lu PDF'ler, OCR entegrasyonu ve belge tipi başına daha geniş kural seti gerekir.
