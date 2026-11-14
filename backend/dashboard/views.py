from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.decorators import staff_required


@staff_required
@require_GET
def index(request):
    return render(request, "dashboard/index.html")


@staff_required
@require_GET
def books(request):
    return render(request, "dashboard/books.html")


@staff_required
@require_GET
def orders(request):
    return render(request, "dashboard/orders.html")


@staff_required
@require_GET
def accounts(request):
    return render(request, "dashboard/accounts.html")


@staff_required
@require_GET
def logs(request):
    return render(request, "dashboard/logs.html")


@staff_required
@require_GET
def profile(request):
    return render(request, "dashboard/profile.html")
