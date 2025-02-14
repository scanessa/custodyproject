# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 15:37:25 2023

@author: hoffmann
"""

import cv2
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", type=str, default="sample_sign_1.png",
	help="path to the input image")
args = vars(ap.parse_args())

# load the input image and display it to our screen
image = cv2.imread(args["image"])
cv2.imshow("Original", image)

# crop the input image and display it to our screen
face = image[317:833, 0:3305]
cv2.imshow("Face", face)
cv2.waitKey(0)
