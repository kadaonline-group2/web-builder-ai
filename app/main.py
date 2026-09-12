from fastapi import FastAPI
from app.routes.generate import router as generate_router

app = FastAPI(title="AI Website Builder for UMKM")
app.include_router(generate_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
