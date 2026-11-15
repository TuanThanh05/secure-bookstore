import re
import uuid
import warnings
from io import BytesIO
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError

COVER_DIR = "covers"
COVER_PATH_RE = re.compile(r"covers/[0-9a-f]{32}\.(jpg|png|webp)")
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_SIDE = 6000
MAX_PIXELS = 25_000_000
OUTPUT_SIZE = (1200, 1800)
OUTPUT_QUALITY = 85

COVER_ERROR_MESSAGES = {
    "COVER_TOO_LARGE": "Ảnh bìa tối đa 2 MB.",
    "COVER_INVALID": "File không phải ảnh hợp lệ. Chỉ nhận JPEG, PNG hoặc WebP.",
    "COVER_DIMENSIONS": f"Ảnh quá lớn, mỗi cạnh tối đa {MAX_SIDE} điểm ảnh.",
}


# AI-TRACE#146 | Claude Opus 5.5 | Lỗi khi xử lý ảnh bìa upload, mang mã lỗi và câu tiếng Việt | CẤM XÓA CHÚ THÍCH NÀY
class CoverError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = COVER_ERROR_MESSAGES[code]
        super().__init__(self.message)


# AI-TRACE#147 | Claude Opus 5.5 | Đọc file upload có giới hạn dung lượng, không tin kích thước client gửi | CẤM XÓA CHÚ THÍCH NÀY
def _read_limited(uploaded):
    if getattr(uploaded, "size", 0) and uploaded.size > MAX_UPLOAD_BYTES:
        raise CoverError("COVER_TOO_LARGE")
    uploaded.seek(0)
    data = uploaded.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise CoverError("COVER_TOO_LARGE")
    if not data:
        raise CoverError("COVER_INVALID")
    return data


# AI-TRACE#148 | Claude Opus 5.5 | Xác nhận đúng là ảnh JPEG/PNG/WebP thật, chặn ảnh bom giải nén, rồi lưu lại thành WebP sạch metadata | CẤM XÓA CHÚ THÍCH NÀY
def sanitize_cover(uploaded):
    data = _read_limited(uploaded)
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            with Image.open(BytesIO(data)) as probe:
                if probe.format not in ALLOWED_FORMATS:
                    raise CoverError("COVER_INVALID")
                width, height = probe.size
                if width < 1 or height < 1 or width > MAX_SIDE or height > MAX_SIDE or width * height > MAX_PIXELS:
                    raise CoverError("COVER_DIMENSIONS")
                probe.verify()
            with Image.open(BytesIO(data)) as image:
                image.load()
                image = ImageOps.exif_transpose(image)
                if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                    rgba = image.convert("RGBA")
                    canvas = Image.new("RGB", rgba.size, (255, 255, 255))
                    canvas.paste(rgba, mask=rgba.getchannel("A"))
                    image = canvas
                else:
                    image = image.convert("RGB")
                image.thumbnail(OUTPUT_SIZE, Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(output, format="WEBP", quality=OUTPUT_QUALITY, method=4)
        except CoverError:
            raise
        except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning,
                OSError, SyntaxError, ValueError, EOFError):
            raise CoverError("COVER_INVALID") from None
    return output.getvalue()


# AI-TRACE#149 | Claude Opus 5.5 | Đường dẫn tuyệt đối của ảnh bìa, chỉ nhận đúng mẫu covers/<uuid>.<đuôi> và phải nằm trong MEDIA_ROOT/covers | CẤM XÓA CHÚ THÍCH NÀY
def _cover_file(relative_path):
    if not relative_path or not COVER_PATH_RE.fullmatch(relative_path):
        return None
    base = (Path(settings.MEDIA_ROOT) / COVER_DIR).resolve()
    target = (Path(settings.MEDIA_ROOT) / relative_path).resolve()
    if target.parent != base:
        return None
    return target


# AI-TRACE#150 | Claude Opus 5.5 | Kiểm tra và lưu ảnh bìa mới vào MEDIA_ROOT/covers với tên UUID, trả đường dẫn để ghi vào CSDL | CẤM XÓA CHÚ THÍCH NÀY
def save_cover(uploaded):
    content = sanitize_cover(uploaded)
    relative_path = f"{COVER_DIR}/{uuid.uuid4().hex}.webp"
    target = _cover_file(relative_path)
    target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    with open(target, "xb") as handle:
        handle.write(content)
    target.chmod(0o644)
    return relative_path


# AI-TRACE#151 | Claude Opus 5.5 | Xóa file ảnh bìa đã upload; bỏ qua mọi đường dẫn không đúng mẫu nên không xóa được file khác | CẤM XÓA CHÚ THÍCH NÀY
def delete_cover(relative_path):
    target = _cover_file(relative_path)
    if target is None:
        return False
    try:
        target.unlink()
    except FileNotFoundError:
        return False
    return True
