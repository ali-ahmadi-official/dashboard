class CSPFrameAncestorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_ancestor = "http://127.0.0.1:5500"

    def __call__(self, request):
        response = self.get_response(request)

        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']

        csp_value = f"frame-ancestors 'self' {self.allowed_ancestor};"
        response['Content-Security-Policy'] = csp_value

        return response
