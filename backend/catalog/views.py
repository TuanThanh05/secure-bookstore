"""View của app catalog.

Quy ước: view giữ mỏng, chỉ làm 3 việc
  1. Kiểm tra quyền (lớp 1): @login_required, @permission_required, lọc theo request.user
  2. Gọi form (kiểm tra đầu vào) hoặc services.py (logic nghiệp vụ, gọi stored procedure)
  3. render() hoặc redirect()
"""
from django.shortcuts import render
from django.views.decorators.http import require_safe


@require_safe  # chỉ cho GET/HEAD; trang chỉ đọc không nhận POST
def home(request):
    """Trang chủ tạm của bộ khung. Sau này lấy danh sách sách từ view v_public_books."""
    return render(request, "shop/home.html")
