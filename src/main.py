#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)  

load_dotenv()

from app.ingest_rss import router as rss_router
from app.services.nlp import router as nlp_router
from app.services.vector_api import router as c3_router
from app2 import chat_api

app = FastAPI(title="ActuLLM (C1+C2+C3+C4)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# C1 + C2 + C3
app.include_router(rss_router)
app.include_router(nlp_router)
app.include_router(c3_router)


app.include_router(chat_api.app.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)