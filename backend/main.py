from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.process_notes import router as notes_router
from api.summarize_email import router as email_router
from api.qa import router as qa_router

load_dotenv()

app = FastAPI(title="ClarityDesk API")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes_router, prefix="/api")
app.include_router(email_router, prefix="/api")
app.include_router(qa_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
