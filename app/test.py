import requests

url = 'http://127.0.0.1:8000/generate_lip_sync_video/'

headers = {
    'accept': 'application/json'
}

files = {
    'text': (None, 'hello ram'),
    'language': (None, 'en'),
    'video': ('1.mp4', open('website/videos/2.mp4', 'rb'), 'video/mp4')
}

response = requests.post(url, headers=headers, files=files)

if response.status_code == 200:
    json_response = response.json()
    print(json_response)
    # process the JSON response here
else:
    print(f'Request failed with status code {response.status_code}')
    print(response.text)
