# error_middleware.py
import logging
from django.utils.deprecation import MiddlewareMixin

from ERRORS import send_error_to_telegram


class ErrorReportingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        error_message = f"Error occurred: {str(exception)}"
        logging.error(error_message)
        send_error_to_telegram(error_message)
        return None
