"""
Locust load testing suite for ClarityDesk.

Simulates concurrent nonprofit users interacting with:
- Health check probes (/health)
- Document upload (/api/documents)
- RAG Question & Answering (/api/ask)
- Meeting notes structured processing (/api/process-notes)
- Email summarization and action item extraction (/api/summarize-email)

Usage:
    locust -f locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, between, task


class ClarityDeskUser(HttpUser):
    # Simulate realistic user wait time between 1 and 3 seconds
    wait_time = between(1, 3)

    def on_start(self):
        """
        Executed when a simulated user starts.
        Checks backend health before initiating workflow tasks.
        """
        self.client.get("/health", name="/health")

    @task(3)
    def ask_question(self):
        """
        Simulate user querying the RAG knowledge base.
        Weighted higher (3x) as reading/asking is more frequent than uploading.
        """
        payload = {
            "question": "What is the annual fundraising target for the upcoming fiscal year?"
        }
        self.client.post("/api/ask", json=payload, name="/api/ask")

    @task(2)
    def process_meeting_notes(self):
        """
        Simulate user submitting raw meeting notes for structured extraction.
        """
        notes = (
            "Meeting on 2026-10-15 with donors. Alice agreed to follow up on the "
            "pledge matching program by next Friday. Bob will prepare the slide deck."
        )
        self.client.post(
            "/api/process-notes",
            json={"notes": notes},
            name="/api/process-notes",
        )

    @task(2)
    def summarize_email(self):
        """
        Simulate user submitting a donor email for summarization.
        """
        email_text = (
            "Dear Sarah, Thank you for sending the Q3 impact report. Our foundation "
            "is impressed with the outreach numbers. Could you schedule a call next "
            "Tuesday at 2 PM EST to discuss renewing our grant?"
        )
        self.client.post(
            "/api/summarize-email",
            json={"email_content": email_text},
            name="/api/summarize-email",
        )

    @task(1)
    def upload_document(self):
        """
        Simulate uploading a text document to the RAG knowledge base.
        """
        files = {
            "file": ("grant_policy.txt", "Grant policy requires quarterly financial reports.", "text/plain")
        }
        self.client.post("/api/documents", files=files, name="/api/documents")
