from threading import local

_thread_locals = local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store the request in thread local storage
        _thread_locals.request = request
        response = self.get_response(request)
        # Clean up after the request is processed
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response

def get_current_request():
    """
    Returns the current request object from thread local storage.
    Returns None if no request is available.
    """
    return getattr(_thread_locals, 'request', None)