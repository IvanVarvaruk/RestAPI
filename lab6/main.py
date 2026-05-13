from fastapi import FastAPI
from api.endpoints import router as books_router
from api.auth import router as auth_router
from database import engine, Base
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Library API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(books_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)