# https://youtu.be/2miw-69Xb0g

"""
ORIGINAL CODE:
@author: Sreenivas Bhattiprolu
IMAGE CLASSIFICATION USING XGBOOST by extracting features using VGG16 imagenet pretrained weights.
This code explains the process of using XGBoost for image classification
using pretrained weights (VGG16) as feature extractors.
Code last tested on: 
    Tensorflow: 2.2.0
    Keras: 2.3.1
    Python: 3.7
pip install xgboost  
    
XGBClassifier(base_score=0.5, booster='gbtree', colsample_bylevel=1,
              colsample_bynode=1, colsample_bytree=1, gamma=0, gpu_id=-1,
              importance_type='gain', interaction_constraints='',
              learning_rate=0.300000012, max_delta_step=0, max_depth=6,
              min_child_weight=1, missing=nan, monotone_constraints='()',
              n_estimators=100, n_jobs=0, num_parallel_tree=1,
              objective='multi:softprob', random_state=0, reg_alpha=0,
              reg_lambda=1, scale_pos_weight=None, subsample=1,
              tree_method='exact', validate_parameters=1, verbosity=None)

ADAPTED BY:
@author:    Stella Canessa
Edits:      Minor name changes (test_data --> validation_data), code for testing model 
            on unlabeled test data, saved model with Pickle
    
"""

import numpy as np 
import matplotlib.pyplot as plt
import glob
import cv2
import pickle 
import os
import seaborn as sns
from keras.applications.vgg16 import VGG16


# Read input images and assign labels based on folder names
os.chdir('P:/2020/14/Kodning/Scans/classification/rotation/')

SIZE = 256  #Resize images

#Capture training data and labels into respective lists
train_images = []
train_labels = [] 

for directory_path in glob.glob("train/*"):
    label = directory_path.split("\\")[-1]
    print(label)
    for img_path in glob.glob(os.path.join(directory_path, "*.JPG")):
        print(img_path)
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)       
        img = cv2.resize(img, (SIZE, SIZE))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        train_images.append(img)
        train_labels.append(label)

#Convert lists to arrays        
train_images = np.array(train_images)
train_labels = np.array(train_labels)


# Capture test/validation data and labels into respective lists

validation_images = []
validation_labels = [] 
for directory_path in glob.glob("validation/*"):
    fruit_label = directory_path.split("\\")[-1]
    for img_path in glob.glob(os.path.join(directory_path, "*.JPG")):
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (SIZE, SIZE))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        validation_images.append(img)
        validation_labels.append(fruit_label)

#Convert lists to arrays                
validation_images = np.array(validation_images)
validation_labels = np.array(validation_labels)

#Encode labels from text to integers.
from sklearn import preprocessing
le = preprocessing.LabelEncoder()
le.fit(validation_labels)
validation_labels_encoded = le.transform(validation_labels)
le.fit(train_labels)
train_labels_encoded = le.transform(train_labels)

#Split data into validate and train datasets (already split but assigning to meaningful convention)
X_train, y_train, X_valid, y_valid = train_images, train_labels_encoded, validation_images, validation_labels_encoded

# Normalize pixel values to between 0 and 1
X_train, X_valid = X_train / 255.0, X_valid / 255.0

#Load model without classifier/fully connected layers
VGG_model = VGG16(weights='imagenet', include_top=False, input_shape=(SIZE, SIZE, 3))

#Make loaded layers as non-trainable. This is important as we want to work with pre-trained weights
for layer in VGG_model.layers:
	layer.trainable = False
    
VGG_model.summary()  #Trainable parameters will be 0


#Now, let us use features from convolutional network for RF
feature_extractor=VGG_model.predict(X_train)

features = feature_extractor.reshape(feature_extractor.shape[0], -1)

X_for_training = features #This is our X input to RF

#XGBOOST
import xgboost as xgb
model = xgb.XGBClassifier()
model.fit(X_for_training, y_train) #For sklearn no one hot encoding

#Send test data through same feature extractor process
X_validation_feature = VGG_model.predict(X_valid)
X_validation_features = X_validation_feature.reshape(X_validation_feature.shape[0], -1)

#Now predict using the trained RF model. 
prediction = model.predict(X_validation_features)
#Inverse le transform to get original label back. 
prediction = le.inverse_transform(prediction)

#Print overall accuracy
from sklearn import metrics
print ("Accuracy = ", metrics.accuracy_score(validation_labels, prediction))

#Confusion Matrix - verify accuracy of each class
from sklearn.metrics import confusion_matrix

cm = confusion_matrix(validation_labels, prediction)
#print(cm)
sns.heatmap(cm, annot=True)

#Check results on a few select images
n=np.random.randint(0, X_valid.shape[0])
img = X_valid[n]
plt.imshow(img)
input_img = np.expand_dims(img, axis=0) #Expand dims so the input is (num images, x, y, c)
input_img_feature=VGG_model.predict(input_img)
input_img_features=input_img_feature.reshape(input_img_feature.shape[0], -1)
prediction = model.predict(input_img_features)[0] 
prediction = le.inverse_transform([prediction])  #Reverse the label encoder to original name
print("The prediction for this image is: ", prediction)
print("The actual label for this image is: ", validation_labels[n])


###################################################################
#Test model on unlabeled images
test_images = []
for img_path in glob.glob(os.path.join("classification/testing/", "*.JPG")):
    print('IMG PATH: ',img_path)
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (SIZE, SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    test_images.append(img)

#Convert lists to arrays                
test_images = np.array(test_images)

#Get prediction for test image
n=np.random.randint(0, len(test_images))
test_img = test_images[n]
plt.imshow(test_img)
test_input_img = np.expand_dims(test_img, axis=0) #Expand dims so the input is (num images, x, y, c)

test_input_img_feature=VGG_model.predict(test_input_img)
test_input_img_features=test_input_img_feature.reshape(input_img_feature.shape[0], -1)
test_prediction = model.predict(test_input_img_features)[0] 
test_prediction = le.inverse_transform([test_prediction])  #Reverse the label encoder to original name
print("The prediction for this image is: ", test_prediction)


###################################################################
#Save model with Pickle
# pickle.dump(model, open('P:/2020/14/Kodning/Code/custodyproject/machine_learning/MLmodel_img_rotation.pkl', 'wb'))
# pickle.dump(VGG_model, open('P:/2020/14/Kodning/Code/custodyproject/machine_learning/VGG_model.pkl', 'wb'))




