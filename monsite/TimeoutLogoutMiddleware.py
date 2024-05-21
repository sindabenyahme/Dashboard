from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

class TimeoutLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if the user is logged in
        if request.user.is_authenticated:
            # Check if last activity time exists in session
            last_activity_time_str = request.session.get('last_activity_time')
            if last_activity_time_str:
                # Convert string back to datetime object
                last_activity_time = timezone.datetime.fromisoformat(last_activity_time_str)
                # Calculate time elapsed since last activity
                elapsed_time = timezone.now() - last_activity_time
                if elapsed_time.total_seconds() > 60*60*60:  # 60 seconds = 1 minute
                    # Log out user and redirect to login page
                    del request.session['last_activity_time']
                    request.user.logout()
                    return redirect('login')  # Change 'login' to your login URL name
            # Update last activity time
            request.session['last_activity_time'] = timezone.now().isoformat()
        else:
            # If the user is not logged in, redirect to the login page
            if not request.resolver_match or request.resolver_match.url_name != 'login':
                return redirect('login')  # Change 'login' to your login URL name
        
        return response
