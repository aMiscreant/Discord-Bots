import io
import random
import time

import piexif
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageChops


def apply_matrix_style_effect(img: Image.Image) -> Image.Image:
    """
    Applies a high-contrast, green-tinted 'Matrix' visual distortion to the image.
    Includes sharpening, blur, and color enhancement.
    """
    img = img.convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.4))
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    r, g, b = img.split()
    g = g.point(lambda i: min(255, i + 60))
    return Image.merge("RGB", (r, g, b))

def apply_glitch_effect(img: Image.Image) -> Image.Image:
    """
    Simulate a glitch effect by RGB channel shift and line distortion.
    """
    img = img.convert("RGB")
    offset = 5
    r, g, b = img.split()
    r = ImageChops.offset(r, offset, 0)
    b = ImageChops.offset(b, -offset, 0)
    img = Image.merge("RGB", (r, g, b))
    return img.filter(ImageFilter.CONTOUR)

def apply_pixel_sort_effect(img: Image.Image) -> Image.Image:
    """
    Create a corrupted-pixel look by sorting rows or columns slightly.
    """
    img = img.convert("RGB")
    pixels = img.load()
    for y in range(img.height):
        row = [pixels[x, y] for x in range(img.width)]
        random.shuffle(row)
        for x in range(img.width):
            pixels[x, y] = row[x]
    return img

def watermark_image(img: Image.Image, text="Encrypted by StegoBot") -> Image.Image:
    draw = ImageDraw.Draw(img)
    font_size = max(12, int(img.width * 0.03))

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # textbbox returns (left, top, right, bottom)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = (img.width - text_width - 12, img.height - text_height - 8)
    draw.text(position, text, font=font, fill=(0, 255, 0))  # Matrix green

    return img

def steg_process_image(image_bytes: bytes, *, mode: str = "matrix", watermark: bool = True) -> bytes:
    """
    Full stego-safe pipeline with user-selected visual effect:
    - Strip metadata
    - Apply visual effect (matrix, glitch, pixel_sort)
    - Optional watermark
    - Return clean PNG bytes
    """
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")

        if mode == "matrix":
            img = apply_matrix_style_effect(img)
        elif mode == "glitch":
            img = apply_glitch_effect(img)
        elif mode == "pixel_sort":
            img = apply_pixel_sort_effect(img)

        if watermark:
            img = watermark_image(img)

        output = io.BytesIO()
        img.save(output, format="PNG", optimize=True)
        output.seek(0)
        return output.read()

def scrub_image_metadata(image_bytes: bytes) -> bytes:
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        output = io.BytesIO()
        img.save(output, format="PNG", optimize=True)
        return output.getvalue()

def sanitize_image(image_bytes: bytes, scramble_metadata: bool = False) -> bytes:
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        if scramble_metadata:
            fake_exif = {
                "0th": {
                    piexif.ImageIFD.Make: f"DiscordBot_{random.randint(1000,9999)}".encode(),
                    piexif.ImageIFD.Model: f"StegoScrubber_{random.randint(1000,9999)}".encode(),
                    piexif.ImageIFD.Software: b"SecureStego 1.0",
                    piexif.ImageIFD.DateTime: time.strftime("%Y:%m:%d %H:%M:%S").encode()
                },
                "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None
            }
            exif_bytes = piexif.dump(fake_exif)
        else:
            exif_bytes = None

        output = io.BytesIO()
        img.save(output, format="PNG", exif=exif_bytes, optimize=True)
        return output.getvalue()

def steg_scrub_and_mutate(image_bytes: bytes) -> bytes:
    """
    Full steganographic-safe pipeline:
    - Strips all metadata
    - Applies Matrix-style visual distortion
    - Adds watermark ("Encrypted by StegoBot")
    - Outputs clean PNG bytes
    """
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")

        # Apply Matrix effect
        img = apply_matrix_style_effect(img)

        # Add watermark
        img = watermark_image(img)

        # Save scrubbed image with no metadata
        output = io.BytesIO()
        img.save(output, format="PNG", optimize=True)
        output.seek(0)
        return output.read()

def lsb_encode(img: Image.Image, message: str) -> Image.Image:
    binary_message = ''.join(format(ord(c), '08b') for c in message) + '00000000'  # Null terminator
    pixels = img.load()
    width, height = img.size
    msg_index = 0
    msg_len = len(binary_message)

    for y in range(height):
        for x in range(width):
            if msg_index >= msg_len:
                return img
            r, g, b = pixels[x, y]
            # Modify least significant bit of red channel
            r = (r & ~1) | int(binary_message[msg_index])
            msg_index += 1
            # Optionally use green and blue channels if message longer
            if msg_index < msg_len:
                g = (g & ~1) | int(binary_message[msg_index])
                msg_index += 1
            if msg_index < msg_len:
                b = (b & ~1) | int(binary_message[msg_index])
                msg_index += 1
            pixels[x, y] = (r, g, b)
    return img



def lsb_decode(img: Image.Image) -> str:
    pixels = img.load()
    width, height = img.size
    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits.append(str(r & 1))
            bits.append(str(g & 1))
            bits.append(str(b & 1))
    bits = ''.join(bits)
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        if byte == '00000000':  # Null terminator
            break
        chars.append(chr(int(byte, 2)))
    return ''.join(chars)
