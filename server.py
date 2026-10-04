"""FastAPI backend - RAG pipeline ile chatbot API."""
import json, os, traceback
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
import chromadb
import config
from indexer import OllamaEmbedder, build_index
from data_processor import DataProcessor

app = FastAPI(title="AHIEN AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals
db_client = None
collection = None
embedder = None
dataset_stats = None

SYSTEM_PROMPT = """Sen AHIEN AI Tıbbi Yapay Zeka Asistanısın.

GÖREV:
Tıbbi hasta veri setindeki bilgileri kullanarak sağlık profesyonellerine ve hastalara yanıt vermek.

KENDİNİ TANITIM:
"Kimsin?" veya "Sen kimsin?" sorulduğunda şu şekilde cevap ver:
"Ben AHIEN AI, onkoloji hasta verileri üzerinde çalışan bir tıbbi yapay zeka asistanıyım. 5 farklı kanser türüne ait hasta profilleri, laboratuvar sonuçları, ilaç tedavileri ve tıbbi işlemler hakkında sorularınızı yanıtlayabilirim."

"Bu projeyi kim yaptı?" veya "Seni kim yaptı?" veya "Kim oluşturdu?" sorulduğunda:
"Bu proje SOL CADENTE takımı tarafından oluşturulmuştur. Sağlık ve teknoloji alanında yenilikçi çözümler geliştirmekteyiz."

KURALLAR:

1. YALNIZCA veri setindeki bilgilere dayanarak cevap ver. Uydurma, varsayıma dayalı veya veri setinde olmayan hiçbir bilgi verme.
2. Veri setinde bulunmayan bilgiler için "Bu bilgi mevcut veri setinde bulunmamaktadır" de.
3. Kullanıcının sorduğu dilde yanıt ver (Türkçe, İngilizce, Almanca, Arapça, Rusça, vb.). Aynı dili kullan.
4. Tıbbi terimler ve jargonlar varsa hemen parantez içinde veya altında açıkla.
5. İstatistiksel sorularda (ortalama, yüzde, sayı) mümkünse kesin rakamlar sun.
6. Tanı, tedavi veya ilaç önerisi yapma. Sadece verileri özetle ve açıkla. Tıbbi karar hekime bırak.
7. Yanıtlarını profesyonel, net ve bilgilendirici tut.
8. Markdown format kullan (başlıklar ##, listeler -, kalın **metin**).
9. Her yanıtın sonunda "[Kaynak: Hasta #ID - Veri Tipi]" formatında kullandığın verileri belirt. (EN: "[Source: Patient #ID - Data Type]")
10. GÜVENLİK: Yanlış veya eksik bilgi riski varsa "Bu konuda kesin bilgi için uzman hekime danışın" uyarısı ekle.

VERİ SETİ:
- ~500 onkoloji hastası
- Kanser türleri: Karaciğer, Meme, Multipl Miyelom, Over, Prostat
- Veri tipleri: Hasta profili, laboratuvar sonuçları (HbA1c, Üre, Kreatinin, Karaciğer enzimleri, elektrolitler, CRP), ilaç tedavileri, tıbbi işlemler, epikriz/özet

ENGLISH VERSION:
- ~500 oncology patients
- Cancer types: Liver, Breast, Multiple Myeloma, Ovarian, Prostat
- Data types: Patient profile, lab results (HbA1c, Urea, Creatinine, Liver enzymes, electrolytes, CRP), medication treatments, medical procedures, discharge summary"""

@app.on_event("startup")
async def startup():
    global db_client, collection, embedder, dataset_stats
    embedder = OllamaEmbedder()

    db_client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
    existing = [c.name for c in db_client.list_collections()]
    if config.CHROMA_COLLECTION not in existing:
        print("⚠️  ChromaDB indeksi bulunamadı. Önce 'python indexer.py' çalıştırın.")
        collection = None
    else:
        collection = db_client.get_collection(config.CHROMA_COLLECTION)
        print(f"✅ ChromaDB yüklendi: {collection.count()} chunk")

    try:
        _, dataset_stats = DataProcessor(config.EXCEL_PATH).process()
    except Exception:
        dataset_stats = {"total": 500, "kanser": {}, "cinsiyet": {}, "ilac_count": 0, "lab_count": 0}

def retrieve(query: str, top_k: int = None, filter_kanser: str = None):
    if not collection:
        return []
    k = top_k or config.TOP_K_RESULTS
    q_embedding = embedder.embed([query])

    where = None
    if filter_kanser:
        where = {"kanser_turu": filter_kanser}

    results = collection.query(
        query_embeddings=q_embedding,
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    docs = []
    if results and results["documents"]:
        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            docs.append({"text": doc, "meta": meta, "score": 1 - dist})
    return docs

async def stream_ollama(messages: list):
    base = config.get_ollama_base()
    model = config.get_model()
    headers = config.get_headers()
    headers["Content-Type"] = "application/json"

    url = f"{base}/api/chat"
    body = {"model": model, "messages": messages, "stream": True}

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=body, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    done = data.get("done", False)
                    if token:
                        yield f"data: {json.dumps({'token': token})}\n\n"
                    if done:
                        yield f"data: {json.dumps({'done': True})}\n\n"
                        return
                except json.JSONDecodeError:
                    continue

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    question = body.get("message", "").strip()
    filter_kanser = body.get("filter", None)

    if not question:
        return JSONResponse({"error": "Soru boş olamaz"}, status_code=400)

    if not collection:
        return JSONResponse({"error": "Veritabanı henüz indekslenmemiş. Lütfen 'python indexer.py' çalıştırın."}, status_code=503)

    # Retrieve relevant chunks
    docs = retrieve(question, filter_kanser=filter_kanser if filter_kanser != "all" else None)
    context = "\n\n---\n\n".join([d["text"] for d in docs])
    sources = [{"hasta_id": d["meta"]["hasta_id"], "kanser": d["meta"]["kanser_turu"],
                "tip": d["meta"]["chunk_type"], "skor": round(d["score"], 3)} for d in docs]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"BAĞLAM (İlgili Hasta Verileri):\n{context}\n\nKULLANICI SORUSU: {question}"}
    ]

    async def event_stream():
        yield f"data: {json.dumps({'sources': sources})}\n\n"
        try:
            async for chunk in stream_ollama(messages):
                yield chunk
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.get("/api/health")
async def health():
    has_cloud = config.use_cloud()
    has_index = collection is not None and collection.count() > 0
    return {
        "status": "ok",
        "mode": "cloud" if has_cloud else "local",
        "model": config.get_model(),
        "indexed": has_index,
        "chunk_count": collection.count() if has_index else 0,
    }

@app.get("/api/stats")
async def stats():
    return dataset_stats or {}

@app.post("/api/reindex")
async def reindex():
    global collection
    try:
        collection = build_index(force=True)
        return {"status": "ok", "chunks": collection.count()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
