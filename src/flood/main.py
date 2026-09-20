import logging
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from flood.api import router
from flood.core.config import Settings
from flood.db import Base, create_database
from flood.features import FEATURES

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.basicConfig(level=logging.INFO)
        engine, sessions = create_database(settings.database_url)
        try:
            Base.metadata.create_all(engine)  # Local prototype only; migrations are planned.
            app.state.sessions = sessions
            app.state.artifact = None
            if settings.model_path.is_file():
                # This local operator-managed path must never reference an untrusted pickle.
                artifact = joblib.load(settings.model_path)
                if artifact["metadata"]["features"] != FEATURES:
                    raise ValueError("Model feature schema is incompatible")
                app.state.artifact = artifact
            logger.info("Flood API initialized; model_ready=%s", app.state.artifact is not None)
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Flood Risk Prototype", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, error: SQLAlchemyError):
        logger.error("Database operation failed (%s)", type(error).__name__)
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    app.include_router(router)
    return app


app = create_app()
