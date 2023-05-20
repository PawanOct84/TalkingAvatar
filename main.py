import asyncio
import os
import subprocess
import tempfile
import uuid
from pydantic import BaseModel, EmailStr
import httpx
import sqlite3
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from fastapi.staticfiles import StaticFiles
import asyncio
from common import *

# Constants
checkpoint_path = "checkpoints/wav2lip_gan.pth"
root_folder = os.getcwd()
driver_folder = os.path.join(root_folder, "driver")
SENDINBLUE_API_KEY = "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"
SENDINBLUE_SMTP_API_URL = "https://api.sendinblue.com/v3/smtp/email"

# Initialize FastAPI app
app = FastAPI()
app.mount("/results", StaticFiles(directory="results"), name="results")

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model to validate input data
class ServiceRequestInput(BaseModel):
    modelid: int
    text: str
    language: str
    email: EmailStr

# Database setup and creation
def create_database():
    conn = sqlite3.connect('service_requests.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS service_requests
                      (id TEXT PRIMARY KEY,
                       modelid INTEGER,
                       text TEXT,
                       language TEXT,
                       email TEXT)''')
    conn.commit()
    conn.close()

create_database()

# API Endpoints
@app.get("/")
async def main():
    return {"message": "Wav2Lip Video Generation API"}

@app.post("/service_request/")
async def create_service_request(service_request_input: ServiceRequestInput, background_tasks: BackgroundTasks, request: Request):
    service_request_id = uuid.uuid4().hex

    conn = sqlite3.connect('service_requests.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO service_requests (id, modelid, text, language, email) VALUES (?, ?, ?, ?, ?)",
                   (service_request_id, service_request_input.modelid, service_request_input.text, service_request_input.language, service_request_input.email))
    conn.commit()
    conn.close()

    message = send_email(
        to_emails= service_request_input.email,
        subject='Service ID',
        html_content = "Hi " + service_request_id + " is your service id. Thank you"

    )
    # await send_email_notification(service_request_id, service_request_input.email)

    background_tasks.add_task(process_service_request, service_request_id, request)

    return {"service_request_id": service_request_id}

async def process_service_request(service_request_id: str, request: Request):
    conn = sqlite3.connect('service_requests.db')
    cursor = conn.cursor()
    cursor.execute("SELECT modelid, text, language, email FROM service_requests WHERE id=?", (service_request_id,))
    service_request = cursor.fetchone()
    conn.close()

    if service_request:
        modelid, text, language, email = service_request
        try:
            video_url = await generate_lip_sync_video(modelid, text, language, request)
            await send_video_url_email(service_request_id, email, video_url)
        except HTTPException as e:
            print(f"Error processing service request {service_request_id}: {str(e.detail)}")
            # Update the service request record in the database to indicate that an error occurred during processing
            # You can add a new column to the service_requests table to store the error message or a status column to indicate success or failure.

 
async def generate_lip_sync_video(modelid: int, text: str, language: str, request: Request):
    with tempfile.TemporaryDirectory() as temp_dir:
        unique_output_filename = f"output_{uuid.uuid4().hex}.mp4"
        output_file_path = os.path.join(temp_dir, unique_output_filename)
        generated_video_path = os.path.join('results', unique_output_filename)

        tts = gTTS(text, lang=language)
        sound_path = os.path.join(temp_dir, "audio.mp3")
        tts.save(sound_path)

        face_video_path = os.path.join(driver_folder, f"{modelid}.mp4")

        cmd = f"python3 inference.py --checkpoint_path {checkpoint_path} --face {face_video_path} --audio {sound_path} --outfile {generated_video_path}"
        try:
            process = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            print(stdout.decode("utf-8"))
            if process.returncode != 0:
                raise Exception(stderr.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Wav2Lip error: {str(e)}")

        base_url = str(request.base_url).rstrip("/")
        return f"{base_url}/results/{unique_output_filename}"


async def send_email_notification(service_request_id, email):
    print(f"send_email_notification: {email}")
    # return
    email_data = {
    "to": [{"email": email}],
    "sender": {"name": "DeepSnap", "email": "toonist.mobirizer@gmail.com"},
    "subject": "Service Request Received",
    "htmlContent": f"Your service request with ID: {service_request_id} has been received and is being processed.",
    }


    headers = {
        "api-key": SENDINBLUE_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(SENDINBLUE_SMTP_API_URL, json=email_data, headers=headers)
        print(f"send_email_notification: {response.text}")

    if response.status_code != 201:
        print(f"Error sending email: {response.text}")

async def send_video_url_email(service_request_id, email, video_url):
    print(f"send_video_url_email: {video_url}")
    # return
    email_data = {
    "to": [{"email": email}],
    "sender": {"name": "DeepSnap", "email": "toonist.mobirizer@gmail.com"},
    "subject": "Service Request Processed",
    "htmlContent": f"Your service request with ID: {service_request_id} has been processed. The generated video can be accessed at: {video_url}",
    }
    
    headers = {
        "api-key": SENDINBLUE_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(SENDINBLUE_SMTP_API_URL, json=email_data, headers=headers)
        print(f"send_video_url_email: {response.text}")

    if response.status_code != 201:
        print(f"Error sending email: {response.text}")



    message = send_email(
        to_emails= email,
        subject='Video URL',
        # html_content='Hi '+process_service_request+' is your service id </b> <br><br><br><br><br><br> Thank you'
        html_content='Your service request with ID: '+process_service_request+' has been processed. The generated video can be accessed at: '+video_url
    )