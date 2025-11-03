import re
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageTk

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "images"
PROFILE_PIC_PATH = OUTPUT_PATH / "profile_pictures"

# Đảm bảo thư mục lưu ảnh tồn tại

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


def reduce_opacity(image, opacity=1.0):
    if image.mode != "RGBA": image = image.convert("RGBA")  # Đảm bảo ảnh có kênh Alpha
    alpha = image.split()[3]  # Lấy kênh Alpha
    alpha = alpha.point(lambda p: int(p * opacity))  # Điều chỉnh độ trong suốt
    image.putalpha(alpha)
    return image  # Trả về ảnh đã chỉnh sửa


def round_corners(image, radius):
    rounded = Image.new("RGBA", image.size, (0, 0, 0, 0))
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, image.size[0], image.size[1]), radius=radius, fill=255)
    rounded.paste(image, (0, 0), mask)
    return rounded

def load_image(path, opacity=None, size=None, rotate=None, round_corner=None,
               from_url=False):
    try:
        if from_url:
            img = Image.open(BytesIO(path))
        else:
            img = Image.open(relative_to_assets(path))
        if opacity is not None:
            img = reduce_opacity(img, opacity)
        if size:
            img = img.resize(size)
        if rotate:
            img = img.rotate(rotate)
        if round_corner:
            img = round_corners(img, round_corner)
        return ImageTk.PhotoImage(img)
    except FileNotFoundError:
        print(f"Không tìm thấy ảnh: {path}")
        return None

def is_valid_username(username):
    """Kiểm tra username chỉ chứa chữ cái, số, dấu gạch dưới (_), tối thiểu 3 ký tự."""
    return re.match(r"^[a-zA-Z0-9_]{3,}$", username) is not None


def is_valid_email(email):
    """Kiểm tra định dạng email hợp lệ."""
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email) is not None
