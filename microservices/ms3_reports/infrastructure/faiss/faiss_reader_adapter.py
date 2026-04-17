import os
from typing import List, Dict
import gc


class FAISSReaderAdapter:
    """A read-only FAISS adapter with a simple fallback.

    Behavior:
    - If environment variable `MS3_FAISS_INDEX_PATH` is set and faiss is importable,
      attempt to use FAISS. (This is a best-effort implementation; embedding vectors
      must be created externally.)
    - Otherwise, if `MS3_FAISS_DOCS_JSON` is set, load a simple JSON list of docs
      and perform a naive token-overlap scoring to return relevant docs.
    - Otherwise returns an empty list.
    """

    def __init__(self, index_path: str | None = None):
        self.index_path = index_path or os.getenv("MS3_FAISS_INDEX_PATH")
        self.docs_json = os.getenv("MS3_FAISS_DOCS_JSON")
        self._docs_cache = None

    def __enter__(self):
        # load docs if provided
        if self.docs_json and os.path.exists(self.docs_json):
            import json

            with open(self.docs_json, "r", encoding="utf-8") as fh:
                self._docs_cache = json.load(fh)
        # attempt to load FAISS index if available and configured
        self._faiss = None
        self._index = None
        if self.index_path and os.path.exists(self.index_path):
            try:
                import faiss as _faiss

                self._faiss = _faiss
                try:
                    # read_index will load the index into memory; keep a reference
                    self._index = _faiss.read_index(self.index_path)
                except Exception:
                    # If reading the index fails, ensure we don't leave partial state
                    try:
                        del self._index
                    except Exception:
                        pass
                    self._index = None
            except Exception:
                # faiss not available or failed to import; fall back to docs_json
                self._faiss = None
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def query(self, q: str, top_k: int = 5) -> List[Dict]:
        # If we have a simple docs cache, do naive overlap scoring
        if self._docs_cache:
            q_tokens = set(q.lower().split())
            scored = []
            for d in self._docs_cache:
                text = d.get("text", "")
                tokens = set(text.lower().split())
                score = len(q_tokens & tokens)
                scored.append((score, d))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [d for s, d in scored[:top_k] if s > 0]
        # If a FAISS index is available, attempt to perform a search.
        # NOTE: This adapter does not know how to produce embeddings for `q`.
        # If an index exists, we avoid keeping the index open across tasks
        # by loading it in __enter__ and releasing it in close().
        if self._index and self._faiss:
            try:
                # The consumer is expected to provide vectors elsewhere; here
                # we can't convert `q` to a vector, so return empty list to
                # avoid incorrect behavior.
                return []
            except Exception:
                return []

        # No docs and no index: return empty
        return []

    def close(self):
        # Release any loaded resources to avoid file locks in concurrent tasks
        try:
            self._docs_cache = None
        except Exception:
            pass
        try:
            if hasattr(self, "_index") and self._index is not None:
                try:
                    del self._index
                except Exception:
                    pass
                self._index = None
        except Exception:
            pass
        try:
            if hasattr(self, "_faiss") and self._faiss is not None:
                del self._faiss
                self._faiss = None
        except Exception:
            pass
        try:
            gc.collect()
        except Exception:
            pass

