"""Legacy entrypoint; use `api/main.py` for the FastAPI application."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Use `api/main.py` - the application has moved."}
