from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from catalog.book_services import (
    BookError,
    create_book,
    delete_book,
    get_book,
    list_books,
    reduce_book_stock,
    restock_book,
    set_book_active,
    update_book,
)
from catalog.covers import CoverError
from catalog.staff_services import (
    CategoryError,
    create_category,
    delete_category,
    list_categories,
    rename_category,
)
from core.decorators import recent_auth_required, staff_required
from core.security_log import log_event

from .catalog_forms import BookCreateForm, BookEditForm, CategoryForm, StockForm, attach_error

BOOKS_PER_PAGE = 20


def _log_upload_rejected(request, exc):
    if isinstance(exc, CoverError):
        log_event("upload_rejected", request, severity="warning", user=request.user,
                  username=request.user.get_username(), detail={"field": "cover", "code": exc.code})
STATUS_FILTERS = {"hien": True, "an": False}


def _book_or_404(book_id):
    try:
        return get_book(book_id)
    except BookError:
        raise Http404("Không tìm thấy sách") from None


@staff_required
@never_cache
@require_http_methods(["GET"])
def books(request):
    filters = {
        "ten": request.GET.get("ten", "").strip()[:100],
        "tac_gia": request.GET.get("tac_gia", "").strip()[:100],
        "the_loai": request.GET.get("the_loai", "").strip()[:20],
        "trang_thai": request.GET.get("trang_thai", ""),
    }
    if filters["trang_thai"] not in STATUS_FILTERS:
        filters["trang_thai"] = ""
    queryset = list_books(category_id=filters["the_loai"] or None, author=filters["tac_gia"] or None,
                          title=filters["ten"] or None, is_active=STATUS_FILTERS.get(filters["trang_thai"]))
    page = Paginator(queryset, BOOKS_PER_PAGE).get_page(request.GET.get("trang"))
    query = request.GET.copy()
    query.pop("trang", None)
    categories = list_categories()
    names = {c.id: c.name for c in categories}
    for book in page.object_list:
        book.category_name = names.get(book.category_id)
    return render(request, "dashboard/books.html", {
        "page": page,
        "filters": filters,
        "categories": categories,
        "query": query.urlencode(),
        "low_stock": settings.LOW_STOCK_THRESHOLD,
    })


@staff_required
@never_cache
@require_http_methods(["GET", "POST"])
def book_create(request):
    categories = list_categories()
    if request.method == "POST":
        form = BookCreateForm(categories, request.POST, request.FILES)
        if form.is_valid():
            try:
                book_id = create_book(request.user, **form.book_fields(), stock=form.cleaned_data["stock"],
                                      cover_file=form.cleaned_data.get("cover"))
            except (BookError, CoverError) as exc:
                _log_upload_rejected(request, exc)
                attach_error(form, exc)
            else:
                messages.success(request, "Đã thêm sách.")
                return redirect("dashboard:book_edit", book_id=book_id)
    else:
        form = BookCreateForm(categories)
    return render(request, "dashboard/book_create.html", {"form": form, "has_categories": bool(categories)})


@staff_required
@never_cache
@require_http_methods(["GET", "POST"])
def book_edit(request, book_id):
    book = _book_or_404(book_id)
    categories = list_categories()
    if request.method == "POST":
        form = BookEditForm(categories, request.POST, request.FILES)
        if form.is_valid():
            try:
                update_book(request.user, book.id, **form.book_fields(), cover_file=form.cleaned_data.get("cover"),
                            remove_cover=form.cleaned_data["remove_cover"])
            except (BookError, CoverError) as exc:
                _log_upload_rejected(request, exc)
                attach_error(form, exc)
            else:
                messages.success(request, "Đã lưu thông tin sách.")
                return redirect("dashboard:book_edit", book_id=book.id)
    else:
        form = BookEditForm(categories, initial={
            "title": book.title, "author": book.author, "isbn": book.isbn, "category_id": book.category_id,
            "description": book.description, "price": book.price, "cost_price": book.cost_price,
        })
    return render(request, "dashboard/book_edit.html", {
        "book": book,
        "form": form,
        "restock_form": StockForm(prefix="nhap"),
        "reduce_form": StockForm(prefix="giam"),
        "category_name": next((c.name for c in categories if c.id == book.category_id), None),
        "low_stock": settings.LOW_STOCK_THRESHOLD,
    })


def _change_stock(request, book_id, prefix, action, verb):
    book = _book_or_404(book_id)
    form = StockForm(request.POST, prefix=prefix)
    if not form.is_valid():
        messages.error(request, f"{verb.capitalize()}: số lượng phải từ 1 đến 10.000.")
    else:
        quantity = form.cleaned_data["quantity"]
        try:
            new_stock = action(request.user, book.id, quantity)
        except BookError as exc:
            messages.error(request, f"Không {verb} được: {exc.message}")
        else:
            messages.success(request, f"Đã {verb} {quantity} cuốn. Tồn kho hiện tại: {new_stock}.")
    return redirect("dashboard:book_edit", book_id=book.id)


@staff_required
@never_cache
@require_POST
def book_restock(request, book_id):
    return _change_stock(request, book_id, "nhap", restock_book, "nhập thêm")


@staff_required
@never_cache
@require_POST
def book_reduce(request, book_id):
    return _change_stock(request, book_id, "giam", reduce_book_stock, "giảm")


@staff_required
@never_cache
@require_POST
def book_toggle(request, book_id):
    book = _book_or_404(book_id)
    target = request.POST.get("trang_thai")
    if target not in STATUS_FILTERS:
        messages.error(request, "Trạng thái không hợp lệ.")
    else:
        try:
            set_book_active(request.user, book.id, STATUS_FILTERS[target])
        except BookError as exc:
            messages.error(request, exc.message)
        else:
            messages.success(request, "Sách đang hiện trong cửa hàng." if STATUS_FILTERS[target] else "Đã ẩn sách khỏi cửa hàng.")
    return redirect("dashboard:book_edit", book_id=book.id)


@staff_required
@recent_auth_required
@never_cache
@require_http_methods(["GET", "POST"])
def book_delete(request, book_id):
    book = _book_or_404(book_id)
    if book.is_active:
        messages.error(request, "Sách đang hiện. Hãy ẩn sách trước khi xóa.")
        return redirect("dashboard:book_edit", book_id=book.id)
    if request.method == "POST":
        try:
            delete_book(request.user, book.id)
        except BookError as exc:
            messages.error(request, exc.message)
            return redirect("dashboard:book_edit", book_id=book.id)
        messages.success(request, f"Đã xóa sách “{book.title}”.")
        return redirect("dashboard:books")
    return render(request, "dashboard/book_delete.html", {"book": book})


@staff_required
@never_cache
@require_http_methods(["GET", "POST"])
def categories(request):
    form = CategoryForm()
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            try:
                create_category(request.user, form.cleaned_data["name"])
            except CategoryError as exc:
                attach_error(form, exc)
            else:
                messages.success(request, f"Đã thêm thể loại “{form.cleaned_data['name']}”.")
                return redirect("dashboard:categories")
    return render(request, "dashboard/categories.html", {"form": form, "categories": list_categories()})


@staff_required
@never_cache
@require_POST
def category_rename(request, category_id):
    form = CategoryForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Tên thể loại không hợp lệ (1–100 ký tự).")
    else:
        try:
            rename_category(request.user, category_id, form.cleaned_data["name"])
        except CategoryError as exc:
            messages.error(request, exc.message)
        else:
            messages.success(request, "Đã đổi tên thể loại.")
    return redirect("dashboard:categories")


@staff_required
@recent_auth_required
@never_cache
@require_http_methods(["GET", "POST"])
def category_delete(request, category_id):
    category = next((c for c in list_categories() if c.id == category_id), None)
    if category is None:
        raise Http404("Không tìm thấy thể loại")
    if not category.can_delete:
        messages.error(request, "Thể loại còn sách nên không xóa được. Hãy chuyển sách sang thể loại khác trước.")
        return redirect("dashboard:categories")
    if request.method == "POST":
        try:
            delete_category(request.user, category.id)
        except CategoryError as exc:
            messages.error(request, exc.message)
        else:
            messages.success(request, f"Đã xóa thể loại “{category.name}”.")
        return redirect("dashboard:categories")
    return render(request, "dashboard/category_delete.html", {"category": category})
