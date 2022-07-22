# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 13:04:13 2022

@author: ifau-SteCa

This file uses a supervised machine learning algorithm (XGBoost) to classfiy whether a 
page (image) is a court page (part of a case) or an appendix

Code source:
    - Loading data: https://kapernikov.com/tutorial-image-classification-with-scikit-learn/
    - Split into train, validate, test: https://towardsdatascience.com/how-to-split-data-into-three-sets-train-validation-and-test-and-why-e50d22d3e54c
"""

import joblib
from skimage.io import imread
from skimage.transform import resize
import os
from collections import Counter
import numpy as np
from sklearn.model_selection import train_test_split
from matplotlib import pyplot as plt
from keras.applications.vgg16 import VGG16
import seaborn as sns
import pickle 
from sklearn import metrics
import xgboost as xgb
from sklearn.metrics import confusion_matrix
import glob

base_name = 'casepg_appendix'
width = 256
include = {'0', '1'}
data_path = "P:/2020/14/Kodning/Scans/ML_appendix/"

def resize_all(src, pklname, include, width=150, height=None):
    """
    load images from path, resize them and write them as arrays to a dictionary, 
    together with labels and metadata. The dictionary is written to a pickle file 
    named '{pklname}_{width}x{height}px.pkl'.
     
    Parameter
    ---------
    src: str
        path to data
    pklname: str
        path to output file
    width: int
        target width of the image in pixels
    include: set[str]
        set containing str
    """
     
    height = height if height is not None else width
     
    data = dict()
    data['description'] = 'resized ({0}x{1})animal images in rgb'.format(int(width), int(height))
    data['label'] = []
    data['filename'] = []
    data['data'] = []   
     
    pklname = f"{pklname}_{width}x{height}px.pkl"
 
    # read all images in PATH, resize and write to DESTINATION_PATH
    for subdir in os.listdir(src):
        if subdir in include:
            print(subdir)
            current_path = os.path.join(src, subdir)
 
            for file in os.listdir(current_path):
                if file[-3:] in {'jpg', 'png'}:
                    im = imread(os.path.join(current_path, file))
                    im = resize(im, (width, height)) #[:,:,::-1]
                    
                    print(int(subdir), file)
                    
                    data['label'].append(int(subdir))
                    data['filename'].append(file)
                    data['data'].append(im)
 
        joblib.dump(data, pklname)

#resize_all(src=data_path, pklname=base_name, width=width, include=include)

def train_model():
    data = joblib.load(f'{base_name}_{width}x{width}px.pkl')
    
    print('number of samples: ', len(data['data']))
    print('keys: ', list(data.keys()))
    print('description: ', data['description'])
    print('image shape: ', data['data'][0].shape)
    print('labels:', np.unique(data['label']))
     
    Counter(data['label'])
    
    X = np.array(data['data'])
    y = np.array(data['label'])
    
    X_train, X_rem, y_train, y_rem = train_test_split(X,y, train_size=0.8)
    X_valid, X_test, y_valid, y_test = train_test_split(X_rem,y_rem, test_size=0.5)
    
    #Load model without classifier/fully connected layers
    VGG_model = VGG16(weights='imagenet', include_top=False, input_shape=(256, 256, 3))
    
    #Make loaded layers as non-trainable. This is important as we want to work with pre-trained weights
    for layer in VGG_model.layers:
    	layer.trainable = False
        
    VGG_model.summary()  #Trainable parameters will be 0
    
    
    #Now, let us use features from convolutional network for RF
    feature_extractor=VGG_model.predict(X_train)
    
    features = feature_extractor.reshape(feature_extractor.shape[0], -1)
    
    X_for_training = features #This is our X input to RF
    
    #XGBOOST
    model = xgb.XGBClassifier()
    model.fit(X_for_training, y_train) #For sklearn no one hot encoding
    
    #Send test data through same feature extractor process
    X_validation_feature = VGG_model.predict(X_valid)
    X_validation_features = X_validation_feature.reshape(X_validation_feature.shape[0], -1)
    
    #Now predict using the trained RF model. 
    prediction = model.predict(X_validation_features)
    #Inverse le transform to get original label back. 
    pickle.dump(model, open('P:/2020/14/Kodning/Code/custodyproject/machine_learning/MLmodel_img_rotation.pkl', 'wb'))
    
    #Print overall accuracy
    print ("Accuracy = ", metrics.accuracy_score(y_valid, prediction))
    
    return VGG_model

def predict(img_path, VGG_model):
    
    model = pickle.load(open('P:/2020/14/Kodning/Code/custodyproject/machine_learning/MLmodel_img_rotation.pkl', 'rb'))
    
    im = imread(img_path)
    im = resize(im, (256, 256)) #[:,:,::-1]
    input_img = np.expand_dims(im, axis=0)
    input_img_feature=VGG_model.predict(input_img)
    input_img_features=input_img_feature.reshape(input_img_feature.shape[0], -1)
    prediction = model.predict(input_img_features)[0]
    
    return prediction

VGG_model = train_model()

for file in glob.glob("P:/2020/14/Kodning/Scans/ML_appendix/test_small/*.jpg"):
    pred = predict(file, VGG_model)
    print(file, pred)
