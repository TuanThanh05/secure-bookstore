from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

from core.validators import clean_search_query, parse_positive_int

from . import services
from .forms import ReviewForm
from .review_services import ReviewError, get_my_review, list_reviews, save_review


@require_safe
def home(request):
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
        "cart_add_url": None,
    }
    return render(request, "shop/home.html", context)


@require_safe
def about(request):
    return render(request, "shop/about.html")


# AI-TRACE#217 | Claude Opus 5.5 | Dựng trang chi tiết sách: thông tin sách, danh sách đánh giá, form đánh giá theo từng loại người xem | CẤM XÓA CHÚ THÍCH NÀY
def _render_detail(request, book, form=None, open_form=False, status=200):
    user = request.user
    can_review = user.is_authenticated and not user.is_staff
    my_review = get_my_review(user, book.id) if can_review else None
    if form is None and can_review:
        initial = {"rating": my_review.rating, "content": my_review.content} if my_review else {}
        form = ReviewForm(initial=initial)
    return render(request, "shop/book_detail.html", {
        "book": book,
        "reviews": list_reviews(book.id),
        "form": form,
        "my_review": my_review,
        "can_review": can_review,
        "open_form": open_form,
        "login_url": f"{reverse('accounts:login')}?next={reverse('catalog:book_detail', args=[book.id])}",
    }, status=status)


# AI-TRACE#218 | Claude Opus 5.5 | Trang chi tiết sách cho mọi người xem; sách ẩn hoặc không tồn tại trả 404 | CẤM XÓA CHÚ THÍCH NÀY
@require_safe
def book_detail(request, book_id):
    book = services.get_public_book(book_id)
    if book is None:
        raise Http404("Không tìm thấy sách")
    return _render_detail(request, book)


# AI-TRACE#219 | Claude Opus 5.5 | Nhận form gửi/sửa đánh giá (chỉ POST, CSRF, khách đã đăng nhập); lỗi thì hiện lại form, thành công thì quay về trang sách | CẤM XÓA CHÚ THÍCH NÀY
@require_POST
def review_submit(request, book_id):
    detail_url = reverse("catalog:book_detail", args=[book_id])
    if not request.user.is_authenticated:
        return redirect_to_login(detail_url)
    book = services.get_public_book(book_id)
    if book is None:
        raise Http404("Không tìm thấy sách")
    if request.user.is_staff:
        messages.error(request, "Tài khoản quản trị không gửi đánh giá.")
        return redirect(detail_url)
    form = ReviewForm(request.POST)
    if form.is_valid():
        try:
            created = save_review(request, book.id, form.cleaned_data["rating"], form.cleaned_data["content"])
        except ReviewError as exc:
            form.add_error(None, exc.message)
        else:
            messages.success(request, "Cảm ơn bạn đã đánh giá." if created else "Đã cập nhật đánh giá của bạn.")
            return redirect(f"{detail_url}#danh-gia")
    return _render_detail(request, book, form=form, open_form=True, status=400)
