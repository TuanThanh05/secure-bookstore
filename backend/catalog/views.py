"""View của app catalog.

Quy ước: view giữ mỏng, chỉ làm 3 việc
  1. Kiểm tra quyền (lớp 1): @login_required, @permission_required, lọc theo request.user
  2. Gọi form (kiểm tra đầu vào) hoặc services.py (logic nghiệp vụ, gọi stored procedure)
  3. render() hoặc redirect()
"""
from django.shortcuts import render
from django.views.decorators.http import require_safe

from core.validators import clean_search_query, parse_positive_int

from . import services


@require_safe  # chỉ cho GET/HEAD; trang chỉ đọc không nhận POST
def home(request):
    """Trang chủ: tìm kiếm + lọc thể loại + lưới sách.

    ?q=        từ khóa, cắt còn 100 ký tự (mục 3 checklist)
    ?category= id thể loại; không phải số nguyên dương hoặc không tồn tại → bỏ qua
    """
    q = clean_search_query(request.GET.get("q", ""))
    categories = services.list_categories()
    category_id = parse_positive_int(request.GET.get("category", ""))
    if category_id not in {c.id for c in categories}:
        category_id = None

    context = {
        "categories": categories,
        "books": services.list_public_books(category_id=category_id, q=q),
        "current_category": category_id,
        "q": q,
        # Khi app orders có view thêm vào giỏ: reverse("orders:cart_add")
        "cart_add_url": None,
    }
    return render(request, "shop/home.html", context)


@require_safe
def about(request):
    """Trang giới thiệu đồ án."""
    return render(request, "shop/about.html")
