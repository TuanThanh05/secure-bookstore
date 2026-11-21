from django.conf import settings
from django.db import models
from django.templatetags.static import static


class StaffConnectionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().using("staff")


class StaffBook(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13)
    category_id = models.BigIntegerField()
    description = models.TextField(null=True)
    cover_image = models.CharField(max_length=255, null=True)
    price = models.PositiveIntegerField()
    cost_price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField()
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    objects = StaffConnectionManager()

    class Meta:
        managed = False
        db_table = "v_staff_books"
        ordering = ["title", "id"]

    def __str__(self):
        return self.title

    @property
    def cover_url(self):
        if self.cover_image:
            return f"{settings.MEDIA_URL}{self.cover_image}"
        return static(settings.BOOK_DEFAULT_COVER)

    @property
    def can_delete(self):
        return not self.is_active
