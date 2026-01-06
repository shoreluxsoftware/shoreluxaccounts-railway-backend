import os
from django.http import FileResponse, HttpResponseNotFound
from django.conf import settings

class ServeMediaFilesMiddleware:
    """Serve media files in production"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.media_url = settings.MEDIA_URL
        self.media_root = settings.MEDIA_ROOT

    def __call__(self, request):
        # Check if request is for media file
        if request.path.startswith(self.media_url):
            # Extract file path
            file_path = request.path.replace(self.media_url, '')
            full_path = os.path.join(self.media_root, file_path)
            
            # Security: Prevent path traversal
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.media_root)):
                return HttpResponseNotFound("File not found")
            
            # Serve the file
            if os.path.isfile(full_path):
                return FileResponse(open(full_path, 'rb'))
            
            return HttpResponseNotFound("File not found")
        
        return self.get_response(request)