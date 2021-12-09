import cv2, pytesseract, os

print('imported')

os.chdir("P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/Photos/New_pictures")

img = cv2.imread("P:/2020/14/Kodning/Test_scanned_docs_phone_app/Scanned_from_courts/Photos/New_pictures/IMG_0065.jpg")
print(img)

# Adding custom options
custom_config = r'--oem 3 --psm 6'
a = pytesseract.image_to_string(img, config=custom_config)
print(a.split(" "))