"""App payments: Cổng thanh toán giả lập, callback có chữ ký HMAC (API server-to-server)."""
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = "payments"
    verbose_name = "Thanh toán"
