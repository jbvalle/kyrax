import os
import sys
from PIL import Image

def crop_to_square(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        # Calculate new height to match width (square)
        new_height = width
        if height == new_height:
            # Already square, no need to crop
            return
        elif height > new_height:
            # Crop from the bottom
            cropped_img = img.crop((0, 0, width, new_height))
            cropped_img.save(image_path)
            print(f"Cropped {image_path} to 1:1 aspect ratio.")
        else:
            print(f"Image {image_path} is smaller in height than width. Skipping.")

def main(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".jpg", ".jpeg")):
            full_path = os.path.join(folder_path, filename)
            crop_to_square(full_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 crop.py <folder_path>")
        sys.exit(1)

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory.")
        sys.exit(1)

    main(folder)

