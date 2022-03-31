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



#Initialize paths
machine_learning_model_rotation = 'P:/2020/14/Kodning/Code/custodyproject/MLmodel_img_rotation.pkl'
SIZE = 256  #Resize images to conform with ML requirements
target_folder = "P:/2020/14/Tingsratter/Sodertorns/Domar/all_scans/remain/split1"
#target_folder = "P:/2020/14/Kodning/Scans/classification/testing/"
file_ending = "*.JPG"


def read_imgfiles(folder_path, extension):
    """
    Read in all files that are to be rotated
    Input path of the folder and file extension, such as JPG
    Returns list of image files for machine learning classification, list of original images for rotation,
    list of image file paths for saving rotated image
    """
    images_ml = []
    og_images = []
    paths = []
    
    for img_path in glob.glob(os.path.join(folder_path, extension)):
        print(img_path)
        paths.append(img_path)
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        og_images.append(img)
        img = cv2.resize(img, (SIZE, SIZE))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        images_ml.append(img)

    #Convert lists to arrays
    images_ml = np.array(images_ml)
    images_ml = images_ml/255.0

    return og_images, images_ml, paths



def main(machine_learning_model_rotation, target_folder, file_ending):
    """
    Load ML model that classifies rotation degree (0,90,270) trained in upsidedown_classification.py
    Predict rotation of images and rotate images, save under new file
    """

    og_images, images_ml, paths = read_imgfiles(target_folder, file_ending)
    
    model = pickle.load(open(machine_learning_model_rotation, 'rb'))
    VGG_model = VGG16(weights='imagenet', include_top=False, input_shape=(SIZE, SIZE, 3))

    feature = VGG_model.predict(images_ml)
    features = feature.reshape(feature.shape[0], -1)
    prediction = model.predict(features)

    #Replace groups in predict with meaningful rotation values
    rotation = np.where(prediction == 1, 270, prediction)
    rotation = np.where(rotation == 2, 90, rotation)

    #Rotate images
    for im, rot, path in zip(og_images, rotation, paths):
        print(path, rot)
        if rot != 0:
            im_out = imutils.rotate(im, angle=rot)
            cv2.imwrite(path, im_out)



#Execute
main(machine_learning_model_rotation, target_folder, file_ending)
