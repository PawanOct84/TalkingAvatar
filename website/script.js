$(document).ready(function () {
    const apiUrl = 'http://127.0.0.1:8000'; // Replace with your API URL
  
    $('#video-generator-form').submit(function (event) {
        event.preventDefault();
      
        const formData = new FormData();
        formData.append('text', $('#text').val());
        formData.append('language', $('#language').val());
        formData.append('video', $('#video').prop('files')[0]);
      
        $.ajax({
          type: 'POST',
          url: apiUrl + '/generate/',
          data: formData,
          processData: false,
          contentType: false,
          dataType: 'text',
          beforeSend: function () {
            $('#progress-container').show();
            $('#video-container').hide();
          },
          success: function (response) {
            console.log(response);
            $('#progress-container').hide();
            $('#video-container').show();
            $('#generated-video').attr('src',response.video_url);
        },
          error: function (xhr, status, error) {
            console.error('Error generating video:', error);
          },
        });
      });      
});
