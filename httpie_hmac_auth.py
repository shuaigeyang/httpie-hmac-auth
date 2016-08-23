"""
HMAC Auth plugin for HTTPie.

"""
import datetime
import base64
import hashlib
import hmac

from httpie.plugins import AuthPlugin

try:
    import urlparse
except ImportError:
    import urllib.parse

__version__ = '0.3.0'
__author__ = 'Nick Satterly'
__licence__ = 'MIT'


class HmacAuth:
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key.encode('ascii')

    def __call__(self, r):
        method = r.method

        content_type = r.headers.get('content-type')
        if not content_type:
            content_type = ''

        content_md5 = r.headers.get('content-md5')
        if not content_md5:
            if content_type:
                m = hashlib.md5()
                m.update(r.body)
                content_md5 = base64.encodestring(m.digest())
                r.headers['Content-MD5'] = content_md5
            else:
                content_md5 = ''

        httpdate = r.headers.get('date')
        if not httpdate:
            now = datetime.datetime.utcnow()
            httpdate = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
            r.headers['Date'] = httpdate

        url = urlparse.urlparse(r.url)
        path = url.path

        string_to_sign = '\n'.join([method, content_md5, content_type, httpdate, path])
        digest = hmac.new(self.secret_key, string_to_sign, hashlib.sha1).digest()
        signature = base64.encodestring(digest).rstrip()

        if self.access_key == '':
            r.headers['Authorization'] = 'HMAC %s' % signature
        elif self.secret_key == '':
            raise ValueError('HMAC secret key cannot be empty.')
        else:
            r.headers['Authorization'] = 'HMAC %s:%s' % (self.access_key, signature)

        return r


class HmacAuthPlugin(AuthPlugin):

    name = 'HMAC token auth'
    auth_type = 'hmac'
    description = 'Sign requests using a HMAC authentication method like AWS'

    def get_auth(self, access_key, secret_key):
        return HmacAuth(access_key, secret_key)
