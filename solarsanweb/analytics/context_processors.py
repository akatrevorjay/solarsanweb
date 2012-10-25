

def cube(request):
    return {
        #'CUBE_URL': 'https://%s' % request.get_host(),
        'CUBE_URL': 'https://%s/cube' % request.get_host(),
    }
