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

        print("output_file_path---------",output_file_path)
        # Convert text to speech and save the audio file
        tts = gTTS(text, lang=language)
        sound_path = os.path.join(temp_dir, "audio.mp3")
        tts.save(sound_path)
        print("sound_path---------",sound_path)

        # Run Wav2Lip inference
        cmd = f"python inference.py --checkpoint_path {checkpoint_path} --face {video_file_path} --audio {sound_path}"
        try:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"Wav2Lip error: {error_message}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Wav2Lip error: {str(e)}")

        # Copy generated video to results folder
        generated_video_path = os.path.join('results', unique_output_filename)
        shutil.copyfile(os.path.join("results", "result_voice.mp4"), generated_video_path)

        # Return the complete URL of the generated video file
        return JSONResponse(content={"video_url": f"{request.url_for('main')}results/{unique_output_filename}"})

# Route to serve video files from the results folder
@app.get("/results/{video_filename}")
async def serve_video(video_filename: str):
    video_path = os.path.join("results", video_filename)
    if os.path.exists(video_path):
        return FileResponse(video_path, media_type="video/mp4")
    else:
        raise HTTPException(status_code=404, detail="Video file not found")

# Main entry point for the application
@app.get("/")
async def main():
    return {"message": "Wav2Lip Video Generation API"}
