from accounts.profile import decrypt_phone, encrypt_phone
from core.security_log import log_event


def update_staff_profile(request, user, data):
    changed = []
    if data["last_name"] != user.last_name:
        user.last_name = data["last_name"]
        changed.append("last_name")
    if data["first_name"] != user.first_name:
        user.first_name = data["first_name"]
        changed.append("first_name")
    if data["phone"] and data["phone"] != (decrypt_phone(user) or ""):
        user.phone_encrypted = encrypt_phone(user, data["phone"])
        changed.append("phone_encrypted")
    if changed:
        user.save(using="staff", update_fields=changed)
        log_event("profile_updated", request, user=user, username=user.get_username(), detail={"fields": changed})
    return changed
