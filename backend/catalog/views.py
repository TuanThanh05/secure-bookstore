from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.http import Http404, QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_safe

from core.security_log import log_event
from core.validators import clean_search_query, parse_positive_int

from orders.cart_services import CART_MAX_PER_BOOK

from . import services
from .forms import ReviewForm
from .review_services import ReviewError, can_write_review, get_my_review, list_reviews, save_review


BOOKS_PER_PAGE = 12


def page_items(current, last):
    wanted = {1, last, current - 1, current, current + 1}
    if current <= 2:
        wanted.add(3)
    if current >= last - 1:
        wanted.add(last - 2)
    shown = sorted(wanted & set(range(1, last + 1)))
    items = []
    for number in shown:
        if items and number - items[-1] == 2:
            items.append(number - 1)
        elif items and number - items[-1] > 2:
            items.append(None)
        items.append(number)
    return items


@require_safe
def home(request):
    q = clean_search_query(request.GET.get("q", ""))
    categories = services.list_categories()
    category_id = parse_positive_int(request.GET.get("category", ""))
    if category_id not in {c.id for c in categories}:
        category_id = None

    books = services.list_public_books(category_id=category_id, q=q)
    page = Paginator(books, BOOKS_PER_PAGE).get_page(parse_positive_int(request.GET.get("trang", "")) or 1)
    query = QueryDict(mutable=True)
    if q:
        query["q"] = q
    if category_id:
        query["category"] = category_id
    context = {
        "categories": categories,
        "books": page.object_list,
        "total": len(books),
        "page": page,
        "page_items": page_items(page.number, page.paginator.num_pages),
        "page_query": query.urlencode(),
        "current_category": category_id,
        "q": q,
        "cart_add_url": reverse("orders:cart_add"),
    }
    return render(request, "shop/home.html", context)


@require_safe
def about(request):
    return render(request, "shop/about.html")


def _render_detail(request, book, form=None, open_form=False, status=200):
    user = request.user
    is_customer = user.is_authenticated and not user.is_staff
    can_review = is_customer and can_write_review(user, book.id)
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
        "need_purchase": is_customer and not can_review,
        "open_form": open_form,
        "cart_add_url": reverse("orders:cart_add"),
        "cart_max": CART_MAX_PER_BOOK,
        "login_url": f"{reverse('accounts:login')}?next={reverse('catalog:book_detail', args=[book.id])}",
    }, status=status)


@require_safe
def book_detail(request, book_id):
    book = services.get_public_book(book_id)
    if book is None:
        raise Http404("Không tìm thấy sách")
    return _render_detail(request, book)


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
            if exc.code == "NOT_PURCHASED":
                log_event("access_denied", request, severity="warning", user=request.user,
                          username=request.user.get_username(), detail={"kind": "review_not_purchased", "book_id": book.id})
                messages.error(request, exc.message)
                return redirect(f"{detail_url}#danh-gia")
            form.add_error(None, exc.message)
        else:
            messages.success(request, "Cảm ơn bạn đã đánh giá." if created else "Đã cập nhật đánh giá của bạn.")
            return redirect(f"{detail_url}#danh-gia")
    return _render_detail(request, book, form=form, open_form=True, status=400)
