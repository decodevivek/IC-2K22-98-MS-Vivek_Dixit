from tkinter import Tk, filedialog
from PIL import Image, ImageEnhance
import os


def select_image():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[
            ("Image Files", "*.jpg *.jpeg *.png *.bmp *.webp *.tiff"),
            ("All Files", "*.*")
        ]
    )

    return file_path


def auto_enhance(img):
    # Brightness
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.10)

    # Contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.20)

    # Color
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.15)

    # Sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.40)

    return img


def main():
    file_path = select_image()

    if not file_path:
        print("No image selected.")
        return

    try:
        image = Image.open(file_path)

        enhanced = auto_enhance(image)

        folder = os.path.dirname(file_path)
        filename = os.path.basename(file_path)

        output = os.path.join(folder, "enhanced_" + filename)

        enhanced.save(output)

        print("=" * 40)
        print("IMAGE ENHANCED SUCCESSFULLY")
        print("=" * 40)
        print("Original :", file_path)
        print("Saved As :", output)

        enhanced.show()

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()