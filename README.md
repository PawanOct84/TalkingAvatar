# AI-Powered Lip-Sync Video Generation API

This API allows you to generate lip-sync videos using the Wav2Lip model.

## Prerequisites

- Python 3.7 or higher
- Virtualenv
- FFmpeg
  Install FFmpeg with the following command:
  sudo apt-get install ffmpeg

## Installation

1. Create a virtual environment:
   virtualenv env

2. Activate the virtual environment:
   source env/bin/activate

For Windows, use the following command to activate the virtual environment:
   env\Scripts\activate

3. Navigate to the project directory (assuming the project directory is named "AIAvtar"):
    cd AIAvtar

4. Install the required dependencies:
    pip install -r requirements.txt

## Running the API

Start the API server using the following command:

    python -m uvicorn main:app --reload
    This will start the API server on http://127.0.0.1:8000/

## Usage

The API provides the following endpoint to generate lip-sync videos:

- `/generate_lip_sync_video/` (POST)

### Example Request

Make a POST request to the `/generate_lip_sync_video/` endpoint with the following form data:

- text: The text to be converted to speech and used for lip-syncing.
- language: (Optional) The language code for the text (default is "en").
- video: The video file in which the face will be animated.

The response will contain a JSON object with the `video_url` key, which provides the URL to the generated lip-sync video.

**Note:** Please choose a video from the driver folder for testing.

Sample cURL command:

curl -X 'POST'
'http://127.0.0.1:8000/generate_lip_sync_video/'
-H 'accept: application/json'
-H 'Content-Type: multipart/form-data'
-F 'text=hello ram'
-F 'language=en'
-F 'video=@1.mp4;type=video/mp4'

### Sample Response

```json
{
  "video_url": "http://127.0.0.1:8000/results/output_3786ac1d2ea0487f81ec1bcba5bc707e.mp4"
}

### Html Client
python -m http.server 8080
After running the command, open your browser and go to http://localhost:8080. This should load your website from the local web server, which will prevent the CORS policy error.

Make sure your backend server is also running and listening on http://127.0.0.1:8000/generate_lip_sync_video/.


License
MIT License
