
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from app.ingest_rss import router as rss_router
from app.services.nlp import router as nlp_router
from fastapi import FastAPI
from app.ingest_rss import router
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()
app.include_router(router)
app.include_router(rss_router)
app.include_router(nlp_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)