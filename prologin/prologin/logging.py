# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import logging
import json
import requests
import traceback


class HTTPRequestHandler(logging.Handler):
    """
    An exception log handler that makes a HTTP request to `request_url`.
    If the request is passed as the first argument to the log record, request
    data will be provided in the report.
    """

    def __init__(self, request_url, request_method='POST', **kwargs):
        logging.Handler.__init__(self)
        self.request_url = request_url
        self.request_method = request_method
        self.request_kwargs = kwargs
        headers = self.request_kwargs.get('headers', {})
        headers['Content-Type'] = 'application/json'
        self.request_kwargs['headers'] = headers

    def emit(self, record: logging.LogRecord):
        if not record.exc_info:
            return

        try:
            request = record.request
        except Exception:
            request = None

        message = {"request": {"user": request.user.username if request.user.is_authenticated else None,
                               "path": request.get_full_path(),
                               "method": request.method,
                               "meta": {k: repr(v) for k, v in request.META.items() if
                                        k.startswith("HTTP_")}} if request else None,
                   "level": {"name": record.levelname},
                   "traceback": [s if isinstance(s, tuple) else (s.filename, s.lineno, s.name, s.line)
                                 for s in traceback.extract_tb(record.exc_info[2])],
                   "exception": {"value": repr(record.exc_info[1]),
                                 "trace": traceback.format_exception(*record.exc_info)}}

        self.send_report(json.dumps(message))

    def send_report(self, message):
        # Prevent requests from logging (infinite loop)
        logger = logging.getLogger('requests')
        logger.disabled = True
        logger.propagate = False
        try:
            requests.request(self.request_method, url=self.request_url, data=message, **self.request_kwargs)
        except requests.RequestException:
            pass
        finally:
            logger.disabled = False
            logger.propagate = True
