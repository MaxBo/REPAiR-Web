import hmac
#import git
from hashlib import sha1

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import force_bytes

git_dir = r'/home/stefaan/repairdata/Dev/repairweb'
# for testing only:
file = r'/home/stefaan/repairdata/Dev/repairweb/webhook_test.txt'

@csrf_exempt
def payload(request):
    # Do all the security stuff...
    # Verify if request came from GitHub
    forwarded_for = u'{}'.format(request.META.get('HTTP_X_FORWARDED_FOR'))
    client_ip_address = ip_address(forwarded_for)
    whitelist = requests.get('https://api.github.com/meta').json()['hooks']

    for valid_ip in whitelist:
        if client_ip_address in ip_network(valid_ip):
            break
    else:
        return HttpResponseForbidden('Permission denied.')
    # Process the GitHub events
    event = request.META.get('HTTP_X_GITHUB_EVENT', 'ping')

    if event == 'ping':
        return HttpResponse('pong')
    elif event == 'push':
        # ToDo: Max needs to install gitpython
        #g = git.cmd.Git(git_dir)
        #g.pull()
        f = open(file, 'w')
        f.write('got payload')
        f.close()
        return HttpResponse('success')

    # In case we receive an event that's neither a ping or push
    return HttpResponse(status=204)