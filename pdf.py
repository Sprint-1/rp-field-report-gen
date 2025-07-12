import os
import sys
import zipfile
import tempfile
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener
import piexif
from datetime import datetime

register_heif_opener()

def clean_filename(name):
    # remove numbers and special characters, keep only letters
    return re.sub(r'[^A-Za-z ]+', '', name).strip().replace(' ', '')

def get_date_taken(img_path):
    ext = os.path.splitext(img_path)[1].lower()
    try:
        if ext in ['.jpg', '.jpeg']:
            exif_dict = piexif.load(img_path)
            date_str = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
            if date_str:
                return datetime.strptime(date_str.decode(), "%Y:%m:%d %H:%M:%S")
        elif ext == '.heic':
            img = Image.open(img_path)
            exif_data = img.info.get("exif")
            if exif_data:
                exif_dict = piexif.load(exif_data)
                date_str = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
                if date_str:
                    return datetime.strptime(date_str.decode(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None

def make_contact_sheet(images, labels, thumb_size, cols, rows, margin=20, label_height=20):
    sheet_width = cols * thumb_size[0] + (cols + 1) * margin
    sheet_height = rows * (label_height + thumb_size[1]) + (rows + 1) * margin
    sheet = Image.new("RGB", (sheet_width, sheet_height), color="white")
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    i = 0
    for row in range(rows):
        for col in range(cols):
            if i >= len(images):
                break
            x = margin + col * (thumb_size[0] + margin)
            y = margin + row * (label_height + thumb_size[1] + margin)

            try:
                bbox = font.getbbox(labels[i])
                text_width = bbox[2] - bbox[0]
            except AttributeError:
                text_width, _ = font.getsize(labels[i])
            text_x = x + (thumb_size[0] - text_width) // 2
            draw.text((text_x, y), labels[i], fill="black", font=font)
            sheet.paste(images[i], (x, y + label_height))
            i += 1
    return sheet

def create_contact_sheet_pdf_from_folder(folder_path, output_pdf, thumb_width=200, thumb_height=150, cols=4, rows=5):
    files_info = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
                img_path = os.path.join(root, file)
                dt = get_date_taken(img_path)
                files_info.append((file, img_path, dt))

    files_info.sort(key=lambda x: (x[2] is None, x[2]))

    if not files_info:
        print("No image files found.")
        return

    thumbs = []
    labels = []
    for (file, img_path, dt) in files_info:
        try:
            img = Image.open(img_path)
            thumb = ImageOps.pad(img, (thumb_width, thumb_height), color='white')
            if thumb.mode in ("RGBA", "P"):
                thumb = thumb.convert("RGB")
            thumbs.append(thumb)

            date_label = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "No date"
            labels.append(date_label)
            print(f"Adding to PDF: {file} - Date Taken: {date_label}")
        except UnidentifiedImageError:
            print(f"⚠️ Skipping file '{file}' — cannot identify image format.")
        except Exception as e:
            print(f"⚠️ Skipping file '{file}' due to error: {e}")

    if not thumbs:
        print("No valid images to add to PDF.")
        return

    pages = []
    i = 0
    per_page = cols * rows
    while i < len(thumbs):
        page_thumbs = thumbs[i:i+per_page]
        page_labels = labels[i:i+per_page]
        while len(page_thumbs) < per_page:
            blank = Image.new("RGB", (thumb_width, thumb_height), color="white")
            page_thumbs.append(blank)
            page_labels.append("")
        page = make_contact_sheet(page_thumbs, page_labels, (thumb_width, thumb_height), cols, rows)
        pages.append(page)
        i += per_page

    pages[0].save(output_pdf, save_all=True, append_images=pages[1:])
    print(f"\n✅ Contact sheet PDF created at: {output_pdf}")

def main():
    if len(sys.argv) >= 2:
        zip_path = sys.argv[1]
    else:
        zip_path = input("Enter the path to your ZIP file: ")

    if not zip_path.lower().endswith('.zip'):
        print("Please provide a valid ZIP file.")
        sys.exit(1)
    if not os.path.isfile(zip_path):
        print("Provided file does not exist.")
        sys.exit(1)

    zip_folder = os.path.dirname(zip_path)
    base_name = os.path.splitext(os.path.basename(zip_path))[0]
    cleaned_name = clean_filename(base_name)
    output_pdf = os.path.join(zip_folder, f"Field Report - {cleaned_name}.pdf")

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        create_contact_sheet_pdf_from_folder(temp_dir, output_pdf)

if __name__ == "__main__":
    main()
