from django.db import DatabaseError

from core.security_log import log_event

DB_PERMISSION_ERRORS = {
    1044: "DB_ACCESS_DENIED",
    1142: "TABLE_ACCESS_DENIED",
    1143: "COLUMN_ACCESS_DENIED",
    1227: "SPECIFIC_ACCESS_DENIED",
    1370: "PROCEDURE_ACCESS_DENIED",
}


# AI-TRACE#329 | Claude Opus 5.5 | Middleware ghi db_permission_denied (mức critical) khi MySQL từ chối câu lệnh vì thiếu quyền – dấu hiệu tấn công hoặc lỗi phân quyền; lỗi vẫn đi tiếp thành trang 500 | CẤM XÓA CHÚ THÍCH NÀY
class DbPermissionDeniedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, DatabaseError) or not exception.args:
            return None
        code = exception.args[0]
        if code not in DB_PERMISSION_ERRORS:
            return None
        user = getattr(request, "user", None)
        authenticated = user is not None and user.is_authenticated
        log_event("db_permission_denied", request, severity="critical", user=user,
                  username=user.get_username() if authenticated else None,
                  detail={"mysql_code": code, "error": DB_PERMISSION_ERRORS[code]})
        return None
