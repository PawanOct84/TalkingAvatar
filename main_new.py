import asyncio
import os
import subprocess
import tempfile
import uuid
from email.message import EmailMessage
import smtplib
from email.mime.text import MIMEText

import aiosmtplib
import gdown
import sqlite3
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from gtts import gTTS
from pydantic import BaseModel, EmailStr

# Initialize FastAPI app
app = FastAPI()

# Add the following lines after creating the app instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def download_model_from_drive(model_url, output_path):
    gdown.download(model_url, output_path, quiet=False)

# Example usage:
model_url = 'https://drive.google.com/uc?id=1H5ewKXz-qJy1YIL7V-icFukRlsOR5PiP'
output_folder = 'checkpoints'
os.makedirs(output_folder, exist_ok=True)
checkpoint_path = os.path.join(output_folder, 'wav2lip_gan.pth')

if not os.path.exists(checkpoint_path):
    print("Downloading Wav2Lip model...")
    download_model_from_drive(model_url, checkpoint_path)

checkpoint_path = "checkpoints/wav2lip_gan.pth"
root_folder = os.getcwd()
driver_folder = os.path.join(root_folder, "driver")

class ServiceRequestInput(BaseModel):
    modelid: int
    text: str
    language: str
    email: EmailStr

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

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = "toonist.mobirizer@gmail.com"
EMAIL_PASSWORD = ""

# conf = ConnectionConfig(
#     MAIL_USERNAME ="toonist.mobirizer@gmail.com",
#     MAIL_PASSWORD = "",
#     MAIL_FROM = "toonist.mobirizer@gmail.com",
#     MAIL_PORT = 465,
#     MAIL_SERVER = "smtp.gmail.com",
#     MAIL_STARTTLS = False,
#     MAIL_SSL_TLS = True,
#     USE_CREDENTIALS = True,
#     VALIDATE_CERTS = True
# )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.post("/service_request/")
async def create_service_request(service_request_input: ServiceRequestInput, background_tasks: BackgroundTasks, request: Request):
    # Generate a unique service request ID
    service_request_id = uuid.uuid4().hex

    # Save the service request to the database
    conn = sqlite3.connect('service_requests.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO service_requests (id, modelid, text, language, email) VALUES (?, ?, ?, ?, ?)",
                   (service_request_id, service_request_input.modelid, service_request_input.text, service_request_input.language, service_request_input.email))
    conn.commit()
    conn.close()

    # Send an email notification
    await send_email_notification(service_request_id, service_request_input.email)

    # Process the service request in the background
    background_tasks.add_task(process_service_request, service_request_id, request)

    return {"service_request_id": service_request_id}

async def send_email_notification(service_request_id, email):
    msg = MIMEText(f"Your service request with ID: {service_request_id} has been received and is being processed.")
    msg["Subject"] = "Service Request Received"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

async def process_service_request(service_request_id: str, request: Request):
    # Retrieve the service request from the database
    conn = sqlite3.connect('service_requests.db')
    cursor = conn.cursor()
    cursor.execute("SELECT modelid, text, language, email FROM service_requests WHERE id=?", (service_request_id,))
    service_request = cursor.fetchone()
    conn.close()

    if service_request:
        modelid, text, language, email = service_request
        # Process the request and generate the video
        video_url = await generate_lip_sync_video(modelid, text, language, request)

        # Send the video URL to the requester's email
        await send_video_url_email(service_request_id, email, video_url)

async def generate_lip_sync_video(modelid: int, text: str, language: str, request: Request):
    # Create temporary directory to store files
    with tempfile.TemporaryDirectory() as temp_dir:

        # Generate unique output filename
        unique_output_filename = f"output_{uuid.uuid4().hex}.mp4"
        output_file_path = os.path.join(temp_dir, unique_output_filename)
        generated_video_path = os.path.join('results', unique_output_filename)

        # Convert text to speech and save the audio file
        tts = gTTS(text, lang=language)
        sound_path = os.path.join(temp_dir, "audio.mp3")
        tts.save(sound_path)

        # Prepare the face video path
        face_video_path = os.path.join(driver_folder, f"{modelid}.mp4")

        # Run Wav2Lip inference
        cmd = f"python3 inference.py --checkpoint_path {checkpoint_path} --face {face_video_path} --audio {sound_path} --outfile {generated_video_path}"
        try:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"Wav2Lip error: {error_message}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Wav2Lip error: {str(e)}")

        # Return the complete URL of the generated video file
        return f"{request.url_for('main')}{generated_video_path}"


async def send_video_url_email(service_request_id, email, video_url):
    message = EmailMessage()
    message.set_content(f"Your service request with ID: {service_request_id} has been processed. The generated video can be accessed at: {video_url}")
    message["Subject"] = "Service Request Processed"
    message["From"] = EMAIL_ADDRESS
    message["To"] = email

    try:
        async with aiosmtplib.SMTP(EMAIL_HOST, EMAIL_PORT, use_tls=True) as server:
            await server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            await server.send_message(message)
    except Exception as e:
        print(f"Error sending email: {e}")

# Main entry point for the application
@app.get("/")
async def main():
    return {"message": "Wav2Lip Video Generation API"}

