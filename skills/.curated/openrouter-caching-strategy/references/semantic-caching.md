# Semantic Caching

## Semantic Caching

### Embedding-Based Cache

```python
import numpy as np
from openai import OpenAI

# For embeddings (can use OpenRouter or direct)
embedding_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.95):
        self.threshold = similarity_threshold
        self.embeddings = []  # (embedding, prompt, response)

    def _get_embedding(self, text: str) -> list:
        # Note: Use embedding model if available
        # This is a placeholder - OpenRouter may have embedding models
        response = embedding_client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _cosine_similarity(self, a: list, b: list) -> float:
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def get(self, prompt: str) -> str | None:
        if not self.embeddings:
            return None

        query_embedding = self._get_embedding(prompt)

        for emb, cached_prompt, response in self.embeddings:
            similarity = self._cosine_similarity(query_embedding, emb)
            if similarity >= self.threshold:
                return response

        return None

    def set(self, prompt: str, response: str):
        embedding = self._get_embedding(prompt)
        self.embeddings.append((embedding, prompt, response))

semantic_cache = SemanticCache(similarity_threshold=0.95)
```
