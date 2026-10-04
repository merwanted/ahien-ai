# 🧬 AHIEN AI — Onkoloji Klinik Karar Destek RAG Sistemi

<div align="center">

[![Award](https://img.shields.io/badge/Award-4th%20Place%20Finalist%20%F0%9F%8F%85-teal?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)
[![Event](https://img.shields.io/badge/Event-DataMedX%20Hackathon%202-red?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)
[![Location](https://img.shields.io/badge/Host-İstinye%20Üniversitesi-0A66C2?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)
[![Team](https://img.shields.io/badge/Team-SOL%20CADENTE-orange?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)
[![Status](https://img.shields.io/badge/Type-Clinical%20AI%20Prototype-success?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)

<p align="center">
  <b>DataMedX Hackathon 2 (İstinye Üniversitesi) 4.lük Derecesi Kazanan Proje</b><br/>
  <i>Onkoloji hasta kayıtları, laboratuvar testleri ve tedavi protokolleri üzerinde halüsinasyonsuz, kaynak gösteren RAG (Retrieval-Augmented Generation) karar destek asistanı.</i>
</p>

</div>

---

> ⚠️ **Proje Durumu:** Bu depo, **DataMedX Hackathon 2** kapsamında **SOL CADENTE** takımı tarafından 48 saatlik yarışma maratonunda geliştirilmiş ve jüriye sunulmuş **çalışan bir tıbbi karar destek prototipidir (Competition MVP / Research Demo)**. Doğrudan klinik tanı amacıyla kullanılamaz; yarışma sunum ve değerlendirme amacıyla tasarlanmıştır.

---

## 📌 Problem & Klinik Çözüm

### Klinik Zorluk
Onkoloji kliniklerinde hekimler ve sağlık profesyonelleri; yüzlerce hastaya ait karmaşık kan tahlilleri (HbA1c, kreatinin, karaciğer enzimleri vb.), epikriz dökümleri, kemoterapi/ilaç protokolleri ve geçmiş medikal işlemlerle karşılaşır. Standart üretken yapay zekâ (LLM) modelleri tıbbi verilerde **halüsinasyon (uydurma bilgi)** riski taşır ve kaynak gösteremez.

### AHIEN AI Çözümü
**AHIEN AI**, hastaya ait gerçek klinik kayıtları vektör uzayında anlamsal olarak indeksleyen ve dil modellerine katı tıbbi güvenlik kuralları getiren bir **RAG (Retrieval-Augmented Generation)** mimarisidir:
- **Sıfır Halüsinasyon Prensibi:** Model yalnızca vektör veritabanından çekilen doğrulanmış hasta dökümlerine dayanarak yanıt üretir. Veri setinde olmayan bilgiler için açıkça uyarı verir.
- **Kesin Kaynak Gösterimi:** Her yanıtın altında doğrudan `[Kaynak: Hasta #ID - Veri Tipi]` şeklinde doğrulanabilir klinik referans sunar.
- **Çok Modlu Onkoloji Filtreleme:** Karaciğer, Meme, Multipl Miyelom, Over ve Prostat kanseri kategorilerine göre sorguları filtreleyebilir.

---

## 🏗️ Sistem Mimarisi & RAG Boru Hattı

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AHIEN AI RAG MİMARİSİ                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
【 1. VERİ İŞLEME & İNDEKSLEME 】                  【 2. SORGULAMA & ÜRETİM 】
• ~500 Onkoloji Hasta Dosyası                      • Hekim / Kullanıcı Sorusu
• Laboratuvar & Epikriz Ayrıştırma                 • BGE-M3 Anlamsal Vektör Arama
• BGE-M3 Yoğun Vektör Temsili (Dense Embedding)    • ChromaDB Cosine Benzerlik Taraması
• ChromaDB Persistent Vektör Koleksiyonu           • İlgili Bağlamın (Top-K) Çekilmesi
                                                                    │
                                                                    ▼
                                                    【 3. GÜVENLİ LLM ÜRETİMİ 】
                                                    • Katı Tıbbi Prompt Kalkanı
                                                    • FastAPI Server-Sent Events (SSE)
                                                    • Kaynak Referanslı Akış Yanıtı
```

---

## 🔬 Veri Seti Kapsamı

Prototip, hackathon kapsamında sağlanan ~500 onkoloji hastasının klinik verileri üzerinde çalışmaktadır:
- **Kanser Grupları:** Karaciğer, Meme, Multipl Miyelom, Over, Prostat
- **Veri Tipleri:** Demografik profiller, biyokimya laboratuvar sonuçları (HbA1c, Üre, Kreatinin, AST/ALT, Elektrolitler, CRP), ilaç tedavileri, uygulanan medikal prosedürler ve epikriz özetleri.

---

## 🛠️ Teknik Yığın (Tech Stack)

- **Backend & Servis:** Python 3.10+, FastAPI, Uvicorn, Asenkron HTTP (httpx)
- **Vektör Veritabanı:** ChromaDB (Persistent Storage)
- **Embedding Modeli:** BGE-M3 (Yerel çok dilli dense representation)
- **Dil Modeli Motoru:** Ollama (Yerel Qwen/Llama veya Cloud Ollama modelleri)
- **Arayüz (Frontend):** Modern HTML5, CSS3, Vanilla JS (Server-Sent Events / Streaming chat)
- **Veri İşleme:** Pandas, OpenPyXL (`data_processor.py`)

---

## 💻 Yerel Geliştirme ve Çalıştırma

### 1. Gereksinimleri Yükleyin
```bash
git clone https://github.com/merwanted/ahien-ai.git
cd ahien-ai

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Vektör Veritabanını İndeksleyin
```bash
python indexer.py
```

### 3. API & Web Arayüzünü Başlatın
```bash
python server.py
```
Sunucu başladığında tarayıcınızdan `http://localhost:8000` adresine giderek AHIEN AI arayüzünü test edebilirsiniz.

---

## 🏆 Yarışma Başarısı & Takım
Bu proje, **İstinye Üniversitesi** ev sahipliğinde düzenlenen **DataMedX Hackathon 2**'de sunulmuş ve jüri değerlendirmesi sonucunda **4.lük Derecesi** elde etmiştir.

* **Takım:** SOL CADENTE
* **Mert Özemir Rolü:** RAG mimarisi, FastAPI backend altyapısı, ChromaDB vektör indeksleme ve prompt güvenliği tasarımı.
