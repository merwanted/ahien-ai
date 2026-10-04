<p align="center">
  <a href="README.md">🇬🇧 <b>English</b></a> | <a href="README.tr.md">🇹🇷 <b>Türkçe</b></a>
</p>

# 🧬 AHIEN AI — Clinical Oncology Decision Support RAG System

<div align="center">

[![Award](https://img.shields.io/badge/Award-4th%20Place%20Finalist%20%F0%9F%8F%85-teal?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)
[![Event](https://img.shields.io/badge/Event-DataMedX%20Hackathon%202-red?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)
[![Location](https://img.shields.io/badge/Host-%C4%B0stinye%20University-0A66C2?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)
[![Team](https://img.shields.io/badge/Team-SOL%20CADENTE-orange?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)
[![Status](https://img.shields.io/badge/Type-Clinical%20AI%20Prototype-success?style=for-the-badge&labelColor=1a1a1a)](https://github.com/merwanted/ahien-ai)

<p align="center">
  <b>4th Place Winning Clinical Decision Support Prototype at DataMedX Hackathon 2 (İstinye University)</b><br/>
  <i>Retrieval-Augmented Generation (RAG) assistant delivering verifiable, hallucination-guarded clinical answers with explicit patient record citations across oncology labs and therapy protocols.</i>
</p>

</div>

---

> ⚠️ **Project Status:** This repository contains a **functional medical decision support prototype (Competition MVP / Research Demo)** developed by team **SOL CADENTE** during the 48-hour **DataMedX Health Hackathon 2**. It is designed strictly for technical jury evaluation and academic exploration, not for autonomous clinical diagnostic practice.

---

## 📌 Clinical Challenge & Solution Vision

### The Clinical Bottleneck
Oncologists and healthcare practitioners regularly review vast volumes of disparate clinical data per patient: panel biochemistry tests (HbA1c, serum creatinine, hepatic enzymes), longitudinal epicrises, chemotherapy regimens, and historical interventions. Standard generative language models pose critical risks of **medical hallucination** and cannot supply verifiable references to source documents.

### The AHIEN AI Approach
**AHIEN AI** deploys an enterprise-grade **Retrieval-Augmented Generation (RAG)** pipeline enforcing strict clinical safety guardrails:
- **Zero-Hallucination Policy:** The LLM is restricted to answering exclusively using context retrieved from the indexed patient vector space. Out-of-corpus queries return explicit disclaimers.
- **Strict Evidence Citations:** Every assertion includes deterministic citations referencing verified records: `[Source: Patient #ID - Record Category]`.
- **Multimodal Oncology Filtering:** Allows clinicians to segment queries by cancer cohort: Hepatic, Breast, Multiple Myeloma, Ovarian, and Prostate.

---

## 🏗️ System Architecture & RAG Pipeline

```
┌────────────────────────────────────────────────────────────────────────┐
│                         AHIEN AI RAG ARCHITECTURE                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
【 1. DATA PROCESSING & INDEXING 】                 【 2. RETRIEVAL & QUERYING 】
• ~500 Oncology Patient Records                     • Clinician Free-Text Query
• Parsing Blood Panels & Epicrises                  • BGE-M3 Dense Semantic Encoding
• BGE-M3 Dense Embeddings Extraction                • ChromaDB Cosine Similarity Search
• ChromaDB Persistent Vector Collection             • Top-K Clinical Context Assembly
                                                                    │
                                                                    ▼
                                                    【 3. GUARDED GENERATION 】
                                                    • Medical Prompt Safety Shield
                                                    • FastAPI Server-Sent Events (SSE)
                                                    • Real-time Streamed Citations
```

---

## 🔬 Dataset Scope

The prototype indexes structured and unstructured clinical data from ~500 anonymized oncology patient records provided during the competition:
- **Cancer Cohorts:** Liver (Hepatic), Breast, Multiple Myeloma, Ovarian, Prostate.
- **Data Categories:** Demographics, laboratory biochemistry panels (HbA1c, Urea, Creatinine, ALT/AST, Electrolytes, CRP), medication schedules, clinical procedures, and discharge summaries.

---

## 🛠️ Technology Stack

- **Backend & Services:** Python 3.10+, FastAPI, Uvicorn, Asynchronous HTTP (`httpx`)
- **Vector Database:** ChromaDB (Persistent Disk Storage)
- **Embedding Model:** BGE-M3 (Multilingual Dense Vector Representation)
- **Inference Engine:** Ollama (Local quantized models / Qwen / Llama)
- **Frontend HUD:** Modern Semantic HTML5, CSS3, Vanilla JS (Server-Sent Events streaming)
- **Data Engineering:** Pandas, OpenPyXL (`data_processor.py`)

---

## 💻 Local Setup & Execution Guide

### 1. Environment Setup
```bash
git clone https://github.com/merwanted/ahien-ai.git
cd ahien-ai

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Index Clinical Vector Database
```bash
python indexer.py
```

### 3. Launch the API & Web Dashboard
```bash
python server.py
```
Open `http://localhost:8000` in your web browser to interact with the AHIEN AI clinical query interface.

---

## 🏆 Competition Achievement & Team Credits

This prototype achieved **🏅 4th Place** at **DataMedX Hackathon 2** hosted by **İstinye University** following live demonstrations and medical jury assessment.

* **Team:** SOL CADENTE
* **Role of Mert Özemir:** RAG pipeline architecture, FastAPI backend services, ChromaDB vector indexing, and medical prompt safety engineering.
