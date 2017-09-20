import hmac
import git
from hashlib import sha1

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import force_bytes

git_dir = r'F:\Projekte SH\REPAiR-Web'

@csrf_exempt
def hello(request):
    # Do all the security stuff...

    # Process the GitHub events
    event = request.META.get('HTTP_X_GITHUB_EVENT', 'ping')

    if event == 'ping':
        return HttpResponse('pong')
    elif event == 'push':
        # Do something...
        g = git.cmd.Git(git_dir)
        g.pull()
        return HttpResponse('success')

    # In case we receive an event that's neither a ping or push
    return HttpResponse(status=204)