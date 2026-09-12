from fastapi import FastAPI

from smartrouter.api.routes import router as api_router

app = FastAPI(title="SmartRouter", version="1.0.0")

app.include_router(api_router)
