"""Chunk'ları ChromaDB'ye BGE-M3 ile indeksler."""
import sys
import httpx
import chromadb
import config
from data_processor import DataProcessor

class OllamaEmbedder:
    def __init__(self, model=None, base_url=None):
        self.model = model or config.EMBEDDING_MODEL
        self.base_url = base_url or config.OLLAMA_LOCAL_BASE

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = httpx.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model, "input": texts},
            timeout=300.0
        )
        resp.raise_for_status()
        return resp.json()["embeddings"]

def build_index(force=False):
    client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)

    existing = [c.name for c in client.list_collections()]
    if config.CHROMA_COLLECTION in existing:
        if not force:
            print(f"Koleksiyon '{config.CHROMA_COLLECTION}' zaten var. --force ile yeniden oluşturun.")
            return client.get_collection(config.CHROMA_COLLECTION)
        client.delete_collection(config.CHROMA_COLLECTION)
        print("Eski koleksiyon silindi.")

    collection = client.create_collection(
        name=config.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

    print("Excel verisi işleniyor...")
    chunks, stats = DataProcessor(config.EXCEL_PATH).process()
    print(f"Toplam {len(chunks)} chunk oluşturuldu.")

    embedder = OllamaEmbedder()
    batch_size = 8
    total = len(chunks)

    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        texts = [ch["text"] for ch in batch]
        ids = [f"chunk_{i + j}" for j in range(len(batch))]
        metadatas = [
            {
                "hasta_id": str(ch["hasta_id"]),
                "kanser_turu": ch["kanser_turu"],
                "cinsiyet": ch["cinsiyet"],
                "chunk_type": ch["type"],
            }
            for ch in batch
        ]

        try:
            embeddings = embedder.embed(texts)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
        except Exception as e:
            print(f"  HATA batch {i}: {e}")
            continue

        done = min(i + batch_size, total)
        pct = done * 100 // total
        print(f"  İndeksleniyor... {done}/{total} ({pct}%)")

    print(f"\n✅ İndeksleme tamamlandı! {collection.count()} chunk ChromaDB'ye eklendi.")
    print(f"📊 İstatistikler: {stats['total']} hasta, {len(stats['kanser'])} kanser türü")
    return collection

if __name__ == "__main__":
    force = "--force" in sys.argv
    build_index(force=force)
