from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import faiss
import numpy as np


load_dotenv()

client = OpenAI()

DATA_DIR = Path("data")



def load_documents():
    documents = []

    for file_path in DATA_DIR.glob("*.md"):
        text = file_path.read_text(encoding="utf-8").strip()

        documents.append({
            "source": file_path.name,
            "text": text
        })

    return documents

def chunk_documents(documents):
    chunks = []

    for doc in documents:
        paragraphs = doc["text"].split("\n\n")

        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()

            if paragraph:
                chunks.append({
                    "source": doc["source"],
                    "chunk_id": i,
                    "text": paragraph
                })

    return chunks  

def create_embeddings(chunks):
    texts = [chunk["text"] for chunk in chunks]

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    for chunk, item in zip(chunks, response.data):
        chunk["embedding"] = item.embedding

    return chunks

def build_faiss_index(chunks):
    embeddings = np.array(
        [chunk["embedding"] for chunk in chunks],
        dtype="float32"
    )

    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index

def retrieve(query, chunks, index, top_k=3):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[query]
    )

    query_embedding = np.array(
        [response.data[0].embedding],
        dtype="float32"
    )

    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):
        results.append({
            "source": chunks[idx]["source"],
            "chunk_id": chunks[idx]["chunk_id"],
            "text": chunks[idx]["text"],
            "score": float(score)
        })

    return results

def generate_answer(query, results):
    context_parts = []

    for result in results:
        context_parts.append(
            f"Source: {result['source']}\n"
            f"Content: {result['text']}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
Answer the question using only the context below.

If the answer is not in the context, say:
"I don't know based on the provided documents."

Context:
{context}

Question:
{query}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text


documents = load_documents()
chunks = chunk_documents(documents)
chunks = create_embeddings(chunks)

index = build_faiss_index(chunks)

print(f"Loaded {len(documents)} documents.")
print(f"Created {len(chunks)} chunks.")
print(f"Vectors stored in FAISS: {index.ntotal}")


query =  "If the application loses access to its database, what should engineers check first?"

results = retrieve(
    query,
    chunks,
    index,
    top_k=5
)

print(f"\nQuestion: {query}\n")

for rank, result in enumerate(results, start=1):
    print(f"Rank {rank}")
    print(f"Source: {result['source']}")
    print(f"Chunk ID: {result['chunk_id']}")
    print(f"Score: {result['score']:.4f}")
    print(result["text"])
    print("-" * 50)

answer = generate_answer(query, results)

print("\nFinal Answer:")
print(answer)