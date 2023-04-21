from gtts import gTTS
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import subprocess
import shutil
import uuid
import os
import tempfile
import gdown
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
import aiosmtplib
import sqlite3
from email.message import EmailMessage

# Initialize FastAPI app
app = FastAPI()
 
# Add the following lines after creating the app instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to the domain where your front-end is hosted, or use '*' to allow all origins
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



# Define paths for model and driver folder
checkpoint_path = "checkpoints/wav2lip_gan.pth"
root_folder = os.getcwd()
driver_folder = os.path.join(root_folder, "driver")

# Define input data model
class Wav2LipInput(BaseModel):
    text: str
    language: str

class ServiceRequestInput(BaseModel):
    modelid: int
    text: str
    language: str
    email: EmailStr

# Create an SQLite database and service_requests table
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

# Email settings (replace these with your own credentials)
EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = "you@example.com"
EMAIL_PASSWORD = "your-email-password"

# Handle request validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Endpoint to generate lip-sync video
@app.post("/generate_lip_sync_video/")
async def generate_lip_sync_video(request: Request, text: str = Form(...), language: str = Form("en"), video: UploadFile = File(...)):
    # Create temporary directory to store files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded video file to temp directory
        video_file_path = os.path.join(temp_dir, video.filename)
        with open(video_file_path, 'wb') as video_file:
            video_file.write(video.file.read())

        # Generate unique output filename
        unique_output_filename = f"output_{uuid.uuid4().hex}.mp4"
        output_file_path = os.path.join(temp_dir, unique_output_filename)
        generated_video_path = os.path.join('results', unique_output_filename)

        print("output_file_path---------",output_file_path)
        # Convert text to speech and save the audio file
        tts = gTTS(text, lang=language)
        sound_path = os.path.join(temp_dir, "audio.mp3")
        tts.save(sound_path)
        print("sound_path---------",sound_path)

        # Run Wav2Lip inference
        cmd = f"python3 inference.py --checkpoint_path {checkpoint_path} --face {video_file_path} --audio {sound_path} --outfile {generated_video_path}"
        try:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"Wav2Lip error: {error_message}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Wav2Lip error: {str(e)}")
        
        # Return the complete URL of the generated video file
        return JSONResponse(content={"video_url": f"{request.url_for('main')}{generated_video_path}"})

# Route to serve video files from the results folder
@app.get("/results/{video_filename}")
async def serve_video(video_filename: str):
    video_path = os.path.join("results", video_filename)
    if os.path.exists(video_path):
        return FileResponse(video_path, media_type="video/mp4")
    else:
        raise HTTPException(status_code=404, detail="Video file not found")

@app.post("/service_request/")
async def create_service_request(service_request_input: ServiceRequestInput):
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

    return {"service_request_id": service_request_id}


async def send_email_notification(service_request_id, email):
    message = EmailMessage()
    message.set_content(f"Your service request with ID: {service_request_id} has been received and is being processed.")
    message["Subject"] = "Service Request Received"
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
