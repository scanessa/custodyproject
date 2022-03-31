# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 09:55:45 2022

@author: ifau-SteCa
"""
import pickle
import numpy as np
import cv2
import glob
import os
from keras.applications.vgg16 import VGG16
import imutils

SIZE = 256  #Resize images

#Sample image
a_images = []
og_images = []
paths = []

for img_path in glob.glob(os.path.join("P:/2020/14/Kodning/Scans/classification/testing/", "*.JPG")):
    paths.append(img_path)
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    og_images.append(img)
    img = cv2.resize(img, (SIZE, SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    a_images.append(img)

#Convert lists to arrays                
a_images = np.array(a_images)
a_images = a_images/255.0

#Predict
model = pickle.load(open('P:/2020/14/Kodning/Code/custodyproject/MLmodel_img_rotation.pkl', 'rb'))
VGG_model = VGG16(weights='imagenet', include_top=False, input_shape=(SIZE, SIZE, 3))

a_feature = VGG_model.predict(a_images)
a_features = a_feature.reshape(a_feature.shape[0], -1)
a_prediction = model.predict(a_features)

#Replace groups in predict with meaningful rotation values
rotation = np.where(a_prediction == 1, 90, a_prediction)
rotation = np.where(rotation == 2, 270, rotation)

#Rotate images
for im, rot, path in zip(og_images, rotation, paths):
    angle_out = rot
    print(path, angle_out)

    #im_out = imutils.rotate(im, angle=90)
    #cv2.imwrite(path, im_out)
