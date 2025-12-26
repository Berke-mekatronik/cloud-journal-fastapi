from fastapi import FastAPI
from dotenv import load_dotenv
from api.controllers import journal_router
import logging

load_dotenv()

# TODO: Setup basic console logging
# Hint: Use logging.basicConfig() with level=logging.INFO
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI()
app.include_router(journal_router)