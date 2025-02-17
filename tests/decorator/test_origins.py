# -*- coding: utf-8 -*-
"""
    test
    ~~~~
    Flask-CORS is a simple extension to Flask allowing you to support cross
    origin resource sharing (CORS) using a simple decorator.

    :copyright: (c) 2016 by Cory Dolphin.
    :license: MIT, see LICENSE for more details.
"""

from ..base_test import FlaskCorsTestCase
from flask import Flask
import re
from flask_cors import *
from flask_cors.core import *

letters = 'abcdefghijklmnopqrstuvwxyz'  # string.letters is not PY3 compatible

class OriginsTestCase(FlaskCorsTestCase):
    def setUp(self) -> None:
        self.app = Flask(__name__)

        @self.app.route('/')
        @cross_origin()
        def wildcard():
            return 'Welcome!'

        @self.app.route('/test_always_send')
        @cross_origin(always_send=True)
        def test_always_send():
            return 'Welcome!'

        @self.app.route('/test_always_send_no_wildcard')
        @cross_origin(always_send=True, send_wildcard=False)
        def test_always_send_no_wildcard():
            return 'Welcome!'

        @self.app.route('/test_send_wildcard_with_origin')
        @cross_origin(send_wildcard=True)
        def test_send_wildcard_with_origin():
            return 'Welcome!'

        @self.app.route('/test_list')
        @cross_origin(origins=["http://foo.com", "http://bar.com"])
        def test_list():
            return 'Welcome!'

        @self.app.route('/test_string')
        @cross_origin(origins="http://foo.com")
        def test_string():
            return 'Welcome!'

        @self.app.route('/test_set')
        @cross_origin(origins={"http://foo.com", "http://bar.com"})
        def test_set():
            return 'Welcome!'

        @self.app.route('/test_subdomain_regex')
        @cross_origin(origins=r"http?://\w*\.?example\.com:?\d*/?.*")
        def test_subdomain_regex():
            return ''

        @self.app.route('/test_compiled_subdomain_regex')
        @cross_origin(origins=re.compile(r"http?://\w*\.?example\.com:?\d*/?.*"))
        def test_compiled_subdomain_regex():
            return ''

        @self.app.route('/test_regex_list')
        @cross_origin(origins=[r".*.example.com", r".*.otherexample.com"])
        def test_regex_list():
            return ''

        @self.app.route('/test_regex_mixed_list')
        @cross_origin(origins=["http://example.com", r".*.otherexample.com"])
        def test_regex_mixed_list():
            return ''

        @self.app.route('/test_multiple_protocols')
        @cross_origin(origins="https?://example.com")
        def test_multiple_protocols():
            return ''

    def test_defaults_no_origin(self) -> None:
        ''' If there is no Origin header in the request, the
            Access-Control-Allow-Origin header should be '*' by default.
        '''
        for resp in self.iter_responses('/'):
            self.assertEqual(resp.headers.get(ACL_ORIGIN), '*')

    def test_defaults_with_origin(self) -> None:
        ''' If there is an Origin header in the request, the
            Access-Control-Allow-Origin header should be included.
        '''
        for resp in self.iter_responses('/', origin='http://example.com'):
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers.get(ACL_ORIGIN), 'http://example.com')

    def test_always_send_no_wildcard(self) -> None:
        '''
            If send_wildcard=False, but the there is '*' in the
            allowed origins, we should send it anyways.
        '''
        for resp in self.iter_responses('/'):
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers.get(ACL_ORIGIN), '*')

    def test_always_send_no_wildcard_origins(self) -> None:
        for resp in self.iter_responses('/'):
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers.get(ACL_ORIGIN), '*')


    def test_send_wildcard_with_origin(self) -> None:
        ''' If there is an Origin header in the request, the
            Access-Control-Allow-Origin header should be included.
        '''
        for resp in self.iter_responses('/test_send_wildcard_with_origin', origin='http://example.com'):
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers.get(ACL_ORIGIN), '*')

    def test_list_serialized(self) -> None:
        ''' If there is an Origin header in the request, the
            Access-Control-Allow-Origin header should be echoed.
        '''
        resp = self.get('/test_list', origin='http://bar.com')
        self.assertEqual(resp.headers.get(ACL_ORIGIN),'http://bar.com')

    def test_string_serialized(self) -> None:
        ''' If there is an Origin header in the request,
            the Access-Control-Allow-Origin header should be echoed back.
        '''
        resp = self.get('/test_string', origin='http://foo.com')
        self.assertEqual(resp.headers.get(ACL_ORIGIN), 'http://foo.com')

    def test_set_serialized(self) -> None:
        ''' If there is an Origin header in the request,
            the Access-Control-Allow-Origin header should be echoed back.
        '''
        resp = self.get('/test_set', origin='http://bar.com')

        allowed = resp.headers.get(ACL_ORIGIN)
        # Order is not guaranteed
        self.assertEqual(allowed, 'http://bar.com')

    def test_not_matching_origins(self) -> None:
        for resp in self.iter_responses('/test_list',origin="http://bazz.com"):
            self.assertFalse(ACL_ORIGIN in resp.headers)

    def test_subdomain_regex(self) -> None:
        for sub in letters:
            domain = "http://%s.example.com" % sub
            for resp in self.iter_responses('/test_subdomain_regex',
                                            headers={'origin': domain}):
                self.assertEqual(domain, resp.headers.get(ACL_ORIGIN))

    def test_compiled_subdomain_regex(self) -> None:
        for sub in letters:
            domain = "http://%s.example.com" % sub
            for resp in self.iter_responses('/test_compiled_subdomain_regex',
                                            headers={'origin': domain}):
                self.assertEqual(domain, resp.headers.get(ACL_ORIGIN))

    def test_regex_list(self) -> None:
        for parent in 'example.com', 'otherexample.com':
            for sub in letters:
                domain = "http://{}.{}.com".format(sub, parent)
                for resp in self.iter_responses('/test_regex_list',
                                                headers={'origin': domain}):
                    self.assertEqual(domain, resp.headers.get(ACL_ORIGIN))

    def test_regex_mixed_list(self) -> None:
        '''
            Tests  the corner case occurs when the send_always setting is True
            and no Origin header in the request, it is not possible to match
            the regular expression(s) to determine the correct
            Access-Control-Allow-Origin header to be returned. Instead, the
            list of origins is serialized, and any strings which seem like
            regular expressions (e.g. are not a '*' and contain either '*'
            or '?') will be skipped.

            Thus, the list of returned Access-Control-Allow-Origin header
            is guaranteed to be 'null', the origin or "*", as per the w3
            http://www.w3.org/TR/cors/#access-control-allow-origin-response-header

        '''
        for sub in letters:
            domain = "http://%s.otherexample.com" % sub
            for resp in self.iter_responses('/test_regex_mixed_list',
                                            origin=domain):
                self.assertEqual(domain, resp.headers.get(ACL_ORIGIN))

        self.assertEqual("http://example.com",
            self.get('/test_regex_mixed_list', origin='http://example.com').headers.get(ACL_ORIGIN))

    def test_multiple_protocols(self) -> None:
        import logging
        logging.getLogger('flask_cors').level = logging.DEBUG
        resp = self.get('test_multiple_protocols', origin='https://example.com')
        self.assertEqual('https://example.com', resp.headers.get(ACL_ORIGIN))


if __name__ == "__main__":
    unittest.main()
