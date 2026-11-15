"""Logic nghiệp vụ của app dashboard.

Mọi thao tác GHI dữ liệu nghiệp vụ đi qua đây và gọi stored procedure, ví dụ:

    from django.db import connection   # kết nối "default" = app_customer
    # với dashboard: from django.db import connections; connections["staff"]

    with connection.cursor() as cur:
        cur.callproc("sp_ten_thu_tuc", [tham_so_1, tham_so_2])   # tham số truyền riêng, KHÔNG nối chuỗi
        row = cur.fetchone()
"""

from accounts.profile import decrypt_phone, encrypt_phone
from core.security_log import log_event


# AI-TRACE#095 | Claude Opus 5.5 | Lưu họ, tên, SĐT của nhân viên bằng kết nối staff, chỉ ghi cột thay đổi, log tên cột | CẤM XÓA CHÚ THÍCH NÀY
def update_staff_profile(request, user, data):
    changed = []
    if data["last_name"] != user.last_name:
        user.last_name = data["last_name"]
        changed.append("last_name")
    if data["first_name"] != user.first_name:
        user.first_name = data["first_name"]
        changed.append("first_name")
    if data["phone"] and data["phone"] != (decrypt_phone(user) or ""):
        user.phone_encrypted = encrypt_phone(user, data["phone"])
        changed.append("phone_encrypted")
    if changed:
        user.save(using="staff", update_fields=changed)
        log_event("profile_updated", request, user=user, username=user.get_username(), detail={"fields": changed})
    return changed
