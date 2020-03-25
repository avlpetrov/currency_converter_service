from starlette.config import Config

config = Config(".env")

DATABASE_URI = config("DATABASE_URI")
APP_NAME: str = config("APP_NAME", default="FastAPI App")
DEBUG: bool = config("DEBUG", default=False)
