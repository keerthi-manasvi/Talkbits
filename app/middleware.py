"""
Cloudflare sets CF-Connecting-IP (and X-Forwarded-For) to the real visitor
IP; request.META['REMOTE_ADDR'] otherwise reports Cloudflare's edge IP.
This matters for rate limiting, logging, and allauth's login-attempt tracking.
"""


class CloudflareRealIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_ip:
            request.META['REMOTE_ADDR'] = cf_ip
        else:
            forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if forwarded_for:
                # The first entry is the original client; the rest are proxies.
                request.META['REMOTE_ADDR'] = forwarded_for.split(',')[0].strip()
        return self.get_response(request)
