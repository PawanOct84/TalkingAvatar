const form = document.getElementById('lip-sync-form');
const galleryItems = document.querySelectorAll('.gallery-item');
const result = document.getElementById('result');
const generatedVideo = document.getElementById('generated-video');
const progressBarFill = document.querySelector('.progress-bar__fill');

function selectGalleryItem(item) {
  galleryItems.forEach((elem) => {
    if (elem === item) {
      elem.classList.add('selected');
    } else {
      elem.classList.remove('selected');
    }
  });
}

galleryItems.forEach((item) => {
  item.addEventListener('click', () => {
    selectGalleryItem(item);
  });
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const selectedItem = document.querySelector('.gallery-item.selected');
  if (!selectedItem) {
    alert('Please select a video from the gallery.');
    return;
  }

  const videoUrl = selectedItem.dataset.videoUrl;

  const formData = new FormData(form);

  try {
    const videoResponse = await fetch(videoUrl);
    const videoBlob = await videoResponse.blob();
    formData.append('video', videoBlob, 'video.mp4');

    const progressCallback = (event) => {
      if (event.lengthComputable) {
        const percentComplete = (event.loaded / event.total) * 100;
        progressBarFill.style.width = percentComplete + '%';
      }
    };

    const response = await fetch('http://127.0.0.1:8000/generate_lip_sync_video/', {
      method: 'POST',
      body: formData,
      onUploadProgress: progressCallback
    });

    if (response.ok) {
      const data = await response.json();
      generatedVideo.src = data.video_url;
      result.style.display = 'block';
    } else {
      alert('Error generating the lip-sync video. Please try again.');
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error generating the lip-sync video. Please try again.');
  }
});
