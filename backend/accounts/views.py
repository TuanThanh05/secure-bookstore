"""View của app accounts.

Quy ước: view giữ mỏng, chỉ làm 3 việc
  1. Kiểm tra quyền (lớp 1): @login_required, @permission_required, lọc theo request.user
  2. Gọi form (kiểm tra đầu vào) hoặc services.py (logic nghiệp vụ, gọi stored procedure)
  3. render() hoặc redirect()
"""
