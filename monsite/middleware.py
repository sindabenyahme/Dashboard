from django.shortcuts import redirect
from django.urls import reverse

class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if the user is logged in
        if request.user.is_authenticated:
            # If the path is undefined, redirect to 'upload' path
            if not request.resolver_match:
                return redirect('upload')  # Change 'upload' to your upload URL name
        else:
            # If the user is not logged in, redirect to the login page
            if not request.resolver_match or request.resolver_match.url_name != 'login':
                return redirect('login')  # Change 'login' to your login URL name
        
        return response
