# Skill: Retrieval-Augmented Generation (RAG)
# Usage: Use when integrating dynamic data, documentation, or enterprise knowledge bases into an LLM's context.

## 📚 Core RAG Pipeline
1. **Ingestion & Chunking**: 
   - Parse raw documents (PDFs, Markdown, HTML).
   - Split them into semantic chunks. Do not split in the middle of a sentence or code block. Use overlapping chunks (e.g., 500 tokens with 50-token overlap) to preserve context.
2. **Embedding**: Convert the chunks into dense vector representations using models like `text-embedding-3-small` or local BGE models.
3. **Storage**: Store vectors and metadata in a Vector Database (Pinecone, Chroma, Qdrant, pgvector).
4. **Retrieval**: When a user queries, embed the query, perform a similarity search (Cosine/Dot Product) against the DB, and retrieve the top K most relevant chunks.
5. **Generation**: Inject the retrieved chunks into the LLM's prompt as context to ground its answer.

## 🎯 Advanced Retrieval Techniques
- **Hybrid Search**: Combine traditional Keyword search (BM25) with Vector (Semantic) search. Vector search is bad at exact product names/IDs; keyword search solves this.
- **Query Expansion/Rewriting**: Use a fast LLM to rewrite the user's messy query into 3-4 optimal search queries before hitting the vector DB.
- **Re-ranking**: Retrieve a larger pool of documents (e.g., Top 20) with a fast vector search, then use a dedicated Cross-Encoder model (like Cohere Rerank) to accurately sort them to the top 5 before passing to the generator LLM.
- **Metadata Filtering**: Always attach metadata (Date, Author, Project ID) to vectors. Filter by metadata *before* running the similarity search to drastically improve relevance and speed.

## 🚫 RAG Anti-Patterns
- Stuffing too many chunks into the context window causes hallucination and high latency. Only feed the highest-quality, re-ranked text.
- Blindly using generic chunk sizes (e.g., 1000 characters) without respecting semantic boundaries like paragraphs or markdown headers.
