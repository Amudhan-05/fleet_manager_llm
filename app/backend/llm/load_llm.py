import os
from llama_cpp import Llama
from backend.llm.llm_engine import init_llm
MODEL_PATH = os.getenv(
    "LLM_MODEL_PATH",
    "app\\backend\\llm\\driving-coach-f16.gguf"
)

_llm = None

def load_llm_once():
    global _llm

    if _llm is not None:
        return

    print(f">>> Loading LLM from: {MODEL_PATH}")

    llm = Llama(
        model_path=MODEL_PATH,   # ✅ USE ENV VARIABLE
        n_ctx=4096,
        n_threads=8,
        chat_format=None,
        verbose=True
    )

    init_llm(llm)
    _llm = llm
    print(">>> LLM INITIALIZED")
