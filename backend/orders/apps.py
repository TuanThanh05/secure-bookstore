"""App orders: Giỏ hàng, đặt đơn (race condition xử lý trong sp_place_order), lịch sử đơn."""
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = "orders"
    verbose_name = "Đơn hàng"
