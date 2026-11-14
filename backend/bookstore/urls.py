from django.urls import include, path

urlpatterns = [
    path("", include("catalog.urls")),
    path("account/", include("accounts.urls")),
    path("orders/", include("orders.urls")),
    # path("payments/", include("payments.urls")),
    path("dashboard/", include("dashboard.urls")),
]

# Trang lỗi tùy chỉnh (chỉ dùng khi DEBUG = False)
handler400 = "core.views.bad_request"
handler403 = "core.views.permission_denied"
handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"
