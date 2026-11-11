"""Logic nghiệp vụ của app orders.

Mọi thao tác GHI dữ liệu nghiệp vụ đi qua đây và gọi stored procedure, ví dụ:

    from django.db import connection   # kết nối "default" = app_customer
    # với dashboard: from django.db import connections; connections["staff"]

    with connection.cursor() as cur:
        cur.callproc("sp_ten_thu_tuc", [tham_so_1, tham_so_2])   # tham số truyền riêng, KHÔNG nối chuỗi
        row = cur.fetchone()
"""
