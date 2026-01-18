from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core import config
from app.modules.auth import router as auth_router
from app.modules.users import router as users_router
from app.modules.catalog import router as catalog_router
from app.modules.try_on import router as try_router
from app.modules.renders import router as renders_router

app = FastAPI(
    title=config.settings.PROJECT_NAME,
    openapi_url=f"{config.settings.API_V1_STR}/openapi.json"
)

# Mount Static
app.mount("/static", StaticFiles(directory=config.settings.STATIC_DIR), name="static")

# Include Routers
app.include_router(auth_router.router, prefix=f"{config.settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(users_router.router, prefix=f"{config.settings.API_V1_STR}/profile", tags=["Profile"])
app.include_router(catalog_router.router, prefix=f"{config.settings.API_V1_STR}/products", tags=["Products"])
app.include_router(catalog_router.admin_router, prefix=f"{config.settings.API_V1_STR}/admin", tags=["Admin"])
app.include_router(try_router.router, prefix=f"{config.settings.API_V1_STR}/try", tags=["Try"])
app.include_router(renders_router.router, prefix=f"{config.settings.API_V1_STR}/renders", tags=["Renders"])

@app.get("/")
def root():
    return {"message": "Welcome to Fittsee Demo Backend"}
