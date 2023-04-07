Wav2Lip Video Generation API
This repository provides an API to generate lip-sync videos using the Wav2Lip model.

Prerequisites
Python 3.7 or higher
Virtualenv
Installation
Create a virtual environment:

virtualenv env
Activate the virtual environment:

source env/bin/activate
For Windows, use the following command to activate the virtual environment:


env\Scripts\activate
Navigate to the project directory (assuming the project directory is named "AIAvtar"):

cd AIAvtar
Install the required dependencies:

pip install -r requirements.txt
Running the API
Start the API server using the following command:


python -m uvicorn main:app --reload
This will start the API server on http://127.0.0.1:8000/.

Usage
The API provides the following endpoint to generate lip-sync videos:

/generate_lip_sync_video/ (POST)
Example Request
Make a POST request to the /generate_lip_sync_video/ endpoint with the following form data:

text: The text to be converted to speech and used for lip-syncing.
language: (Optional) The language code for the text (default is "en").
video: The video file in which the face will be animated.
The response will contain a JSON object with the video_url key, which provides the URL to the generated lip-sync video.

License
MIT License

