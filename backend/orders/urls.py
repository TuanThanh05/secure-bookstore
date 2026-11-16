from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("cart/", views.cart, name="cart"),
    path("cart/them/", views.cart_add, name="cart_add"),
    path("cart/cap-nhat/", views.cart_update, name="cart_update"),
    path("cart/go/", views.cart_remove, name="cart_remove"),
    path("dat-hang/", views.checkout, name="checkout"),
    path("don/<str:code>/", views.order_detail, name="order_detail"),
]
