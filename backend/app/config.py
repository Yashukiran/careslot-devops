import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://careslot:careslot@localhost:5432/careslot",
)
APP_NAME = "CareSlot API"
APP_VERSION = os.getenv("APP_VERSION", "dev")  # CI sets this to the image tag (git sha)
APP_ENV = os.getenv("APP_ENV", "local")

# comma separated list, only needed when the frontend is served from another origin (vite dev server)
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
