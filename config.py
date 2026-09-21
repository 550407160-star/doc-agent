import os

from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash")

EMBED_BASE_URL = os.getenv("EMBED_BASE_URL") or LLM_BASE_URL
EMBED_API_KEY = os.getenv("EMBED_API_KEY") or LLM_API_KEY
EMBED_MODEL = os.getenv("EMBED_MODEL", "embedding-3")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "4"))

DATA_DIR = os.getenv("DATA_DIR", "./data")
PERSIST_DIR = os.getenv("PERSIST_DIR", "./chroma_db")
