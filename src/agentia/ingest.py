import httpx

BLOG_API = "https://thehyyu-blog.vercel.app/api"
LANGS = ["zh", "en"]


def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        i += size - overlap
        if i >= len(words):
            break
    return chunks


async def fetch_content(slug: str, lang: str, content_type: str = "post") -> str | None:
    """Fetch post or project content for a given language. Returns None if not found or empty."""
    url = f"{BLOG_API}/{content_type}s/{slug}?lang={lang}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    content = resp.json().get(content_type, {}).get("content", "")
    return content if content else None


async def fetch_all_slugs() -> list[tuple[str, str]]:
    """Return list of (slug, type) for all posts and projects."""
    results = []
    async with httpx.AsyncClient(timeout=15) as client:
        for content_type in ("posts", "projects"):
            resp = await client.get(f"{BLOG_API}/{content_type}")
            resp.raise_for_status()
            data = resp.json()
            key = content_type[:-1]  # "posts" -> "post", "projects" -> "project"
            for item in data.get(content_type, []):
                results.append((item["slug"], key))
    return results


async def embed_text(text: str, ollama_base_url: str) -> list[float]:
    async with httpx.AsyncClient(base_url=ollama_base_url, timeout=60) as client:
        resp = await client.post(
            "/api/embeddings",
            json={"model": "bge-m3", "prompt": text},
        )
    resp.raise_for_status()
    return resp.json()["embedding"]
