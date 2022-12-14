# from django.contrib.auth import login
from .models import Session


def ip_session_middleware(get_response):
    def middleware(request):
        session, _ = Session.objects.get_or_create(ip_address=request.META['REMOTE_ADDR'])
        if request.user.is_authenticated and session.user != request.user:
            session.user = request.user
            session.save()
        # elif request.user.is_anonymous and session.user:
        #     login(request, session.user)
        return get_response(request)
    return middleware

