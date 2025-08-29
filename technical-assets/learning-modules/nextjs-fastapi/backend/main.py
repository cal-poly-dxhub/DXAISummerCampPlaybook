# This is the main FastAPI backend file.
# It demonstrates how to set up a simple API with CORS enabled and handle JSON requests using Pydantic models.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create the FastAPI app instance
app = FastAPI()


# Enable CORS so the frontend (on a different port) can call the backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# A simple GET endpoint for testing if the API is running
@app.get("/test")
def read_root():
    return {"message": "Hello, World!"}


# Define a Pydantic model for the expected POST /echo request body
class EchoMessage(BaseModel):
    message: str  # The message field must be a string


# A POST endpoint that echoes back the message sent by the client
@app.post("/echo")
def echo_message(payload: EchoMessage):
    # The payload is automatically parsed and validated as a Message object
    return {"message": f"Api says: {payload.message}"}
