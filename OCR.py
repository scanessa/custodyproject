import fitz
from PIL import Image

input_pdf = "P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/9-01.pdf"
output_name = "P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/9-01IMG.jpg"

zoom = 2 # to increase the resolution
mat = fitz.Matrix(zoom, zoom)

doc = fitz.open(input_pdf)
image_list = []
for page in doc:
    pix = page.getPixmap(matrix = mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    image_list.append(img)
    
if image_list:
    image_list[0].save(
        output_name,
        save_all=True,
        append_images=image_list[1:],
        dpi=(300, 300),
    )


"""
import cv2, pytesseract, os

print('imported')

os.chdir("P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/Photos/New_pictures")

img = cv2.imread("P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/Photos/New_pictures/IMG_0065.jpg")
print(img)

# Adding custom options
custom_config = r'--oem 3 --psm 6'
a = pytesseract.image_to_string(img, config=custom_config)
print(a.split(" "))
"""