import os
import piexif
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

def get_date_taken_piexif(path):
    try:
        exif_dict = piexif.load(path)
        date_str = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
        if date_str:
            return date_str.decode("utf-8")
    except Exception as e:
        pass
    return None

def get_date_taken_heif(path):
    try:
        img = Image.open(path)
        exif_data = img.info.get("exif")
        if exif_data:
            exif_dict = piexif.load(exif_data)
            date_str = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
            if date_str:
                return date_str.decode("utf-8")
    except Exception as e:
        pass
    return None

def main(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if not os.path.isfile(file_path):
            continue
        ext = filename.lower()
        date_taken = None
        if ext.endswith(('.jpg', '.jpeg')):
            date_taken = get_date_taken_piexif(file_path)
        elif ext.endswith('.heic'):
            date_taken = get_date_taken_heif(file_path)
        print(f"{filename}: Date Taken -> {date_taken if date_taken else 'Not Found'}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
    else:
        main(sys.argv[1])
