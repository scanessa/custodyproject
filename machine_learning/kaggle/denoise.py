"""
Denoise pictures/dirty scans
From: https://www.kaggle.com/code/michalbrezk/denoise-images-using-autoencoders-tf-keras/notebook

"""
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import zipfile
import os
import cv2

from sklearn.model_selection import train_test_split

from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, UpSampling2D, Dropout, BatchNormalization, Input
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow as tf


import os
for dirname, _, filenames in os.walk('P:/2020/14/Kodning/Code/custodyproject/machine_learning/kaggle/input/denoising-dirty-documents/'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# path to zipped & working directories
path_zip = 'P:/2020/14/Kodning/Code/custodyproject/machine_learning/kaggle/input/denoising-dirty-documents/'
path = 'P:/2020/14/Kodning/Code/custodyproject/machine_learning/kaggle/input/working/'

denoising_model = ''
checkpoint_filepath = 'P:/2020/14/Kodning/Code/custodyproject/machine_learning/checkpoint.h5'
EPOCHS = 600

# unzip files first to working directory
# We could use also unzipped data source, but why not to learn something new?
with zipfile.ZipFile(path_zip + 'train.zip', 'r') as zip_ref:
    zip_ref.extractall(path)

with zipfile.ZipFile(path_zip + 'test.zip', 'r') as zip_ref:
    zip_ref.extractall(path)  
    
with zipfile.ZipFile(path_zip + 'train_cleaned.zip', 'r') as zip_ref:
    zip_ref.extractall(path)  
    
with zipfile.ZipFile(path_zip + 'sampleSubmission.csv.zip', 'r') as zip_ref:
    zip_ref.extractall(path)  

# store image names in list for later use
train_img = sorted(os.listdir(path + '/train'))
train_cleaned_img = sorted(os.listdir(path + '/train_cleaned'))
test_img = sorted(os.listdir(path + '/test'))



# prepare function
def process_image(path):
    img = cv2.imread(path)
    img = np.asarray(img, dtype="float32")
    img = cv2.resize(img, (540, 420))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = img/255.0
    img = np.reshape(img, (420, 540, 1))
    
    return img

# preprocess images
train = []
train_cleaned = []
test = []

for f in sorted(os.listdir(path + 'train/')):
    train.append(process_image(path + 'train/' + f))

for f in sorted(os.listdir(path + 'train_cleaned/')):
    train_cleaned.append(process_image(path + 'train_cleaned/' + f))
   
for f in sorted(os.listdir(path + 'test/')):
    test.append(process_image(path + 'test/' + f))

plt.figure(figsize=(15,25))
for i in range(0,8,2):
    plt.subplot(4,2,i+1)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(train[i][:,:,0], cmap='gray')
    plt.title('Noise image: {}'.format(train_img[i]))
    
    plt.subplot(4,2,i+2)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(train_cleaned[i][:,:,0], cmap='gray')
    plt.title('Denoised image: {}'.format(train_img[i]))

plt.show()

# convert list to numpy array
X_train = np.asarray(train)
Y_train = np.asarray(train_cleaned)
X_test = np.asarray(test)

X_train, X_val, Y_train, Y_val = train_test_split(X_train, Y_train, test_size=0.15)


def model_learn():
    input_layer = Input(shape=(420, 540, 1))  # we might define (None,None,1) here, but in model summary dims would not be visible
    
    # encoding
    x = Conv2D(64, (3, 3), activation='relu', padding='same')(input_layer)
    x = Conv2D(128, (3, 3), activation='relu', padding='same')(x)
    x = BatchNormalization()(x)

    x = MaxPooling2D((2, 2), padding='same')(x)
    
    x = Dropout(0.5)(x)

    # decoding
    x = Conv2D(128, (3, 3), activation='relu', padding='same')(x)
    x = Conv2D(64, (3, 3), activation='relu', padding='same')(x)
    x = BatchNormalization()(x)

    x = UpSampling2D((2, 2))(x)

    output_layer = Conv2D(1, (3, 3), activation='sigmoid', padding='same')(x)
    model = Model(inputs=[input_layer], outputs=[output_layer])
    model.compile(optimizer='adam' , loss='mean_squared_error', metrics=['mae'])

    return model

#Uncomment if model should be trained, else used model saved with pickle
model = model_learn()

model.summary()

model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_filepath,
        save_weights_only=True,
        monitor='val_accuracy',
        mode='max',
        save_best_only=True)
callback = EarlyStopping(monitor='loss', patience=30)
history = model.fit(X_train, Y_train, validation_data = (X_val, Y_val), epochs=EPOCHS, batch_size=24, verbose=1, callbacks=[model_checkpoint_callback, callback])

# Check how loss & mae went down
epoch_loss = history.history['loss']
epoch_val_loss = history.history['val_loss']
epoch_mae = history.history['mae']
epoch_val_mae = history.history['val_mae']

plt.figure(figsize=(20,6))
plt.subplot(1,2,1)
plt.plot(range(0,len(epoch_loss)), epoch_loss, 'b-', linewidth=2, label='Train Loss')
plt.plot(range(0,len(epoch_val_loss)), epoch_val_loss, 'r-', linewidth=2, label='Val Loss')
plt.title('Evolution of loss on train & validation datasets over epochs')
plt.legend(loc='best')

plt.subplot(1,2,2)
plt.plot(range(0,len(epoch_mae)), epoch_mae, 'b-', linewidth=2, label='Train MAE')
plt.plot(range(0,len(epoch_val_mae)), epoch_val_mae, 'r-', linewidth=2,label='Val MAE')
plt.title('Evolution of MAE on train & validation datasets over epochs')
plt.legend(loc='best')

plt.show()



# predict/clean test images
Y_test = model.predict(X_test, batch_size=16)



plt.figure(figsize=(15,25))
for i in range(0,8,2):
    plt.subplot(4,2,i+1)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(X_test[i][:,:,0], cmap='gray')
    plt.title('Noisy image: {}'.format(test_img[i]))
    
    plt.subplot(4,2,i+2)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(Y_test[i][:,:,0], cmap='gray')
    plt.title('Denoised by autoencoder: {}'.format(test_img[i]))

plt.show()

# Save the entire model to a HDF5 file.
# The '.h5' extension indicates that the model should be saved to HDF5.
model.save('P:/2020/14/Kodning/Code/custodyproject/machine_learning/MLmodel_denoising.h5')



#Load model

savedModel=load_model('MLmodel_denoising.h5')
savedModel.summary()
"""



"""
Taken from: https://www.kaggle.com/code/sushanth1995/image-augmentation-and-neural-encoder-decoder/notebook
"""

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)


import os
import glob 

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as img

import imageio
import imgaug as ia
from imgaug import augmenters as iaa
import cv2

from keras.preprocessing import image
from keras.models import Model, load_model
from tensorflow.keras.optimizers import Adam
from keras.callbacks import EarlyStopping, LearningRateScheduler, ModelCheckpoint
from keras.layers import Input, Dense, Activation, BatchNormalization, Flatten, Conv2D, LeakyReLU
from keras.layers import MaxPooling2D, Dropout, UpSampling2D
from keras import regularizers
import keras.backend as kb
import zipfile
# Input data files are available in the "../input/" directory.
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# Any results you write to the current directory are saved as output.

plt.rcParams['figure.figsize'] = (10.0, 5.0) # set default size of plots

zipfiles = ['train','test','train_cleaned', 'sampleSubmission.csv']

for each_zip in zipfiles:
    with zipfile.ZipFile("P:/2020/14/Kodning/Code/custodyproject/machine_learning/kaggle/input/denoising-dirty-documents/"+each_zip+".zip","r") as z:
        z.extractall(".")
        
        


bsb = img.imread('P:/2020/14/Kodning/Code/custodyproject/machine_learning/kaggle/input/working/train/216.png')
# test = img.imread('../kaggle/working/test/1.png')
plt.imshow(bsb, cmap=plt.cm.gray)



target_width = 540
target_height = 420

def load_image_from_dir(img_path):
    file_list = glob.glob(img_path+'/*.png')
    file_list.sort()
    img_list = np.empty((len(file_list), target_height, target_width, 1))
    for i, fig in enumerate(file_list):
        img = image.load_img(fig, color_mode='grayscale', target_size=(target_height, target_width))
        img_array = image.img_to_array(img).astype('float32')
        img_array = img_array / 255.0
        img_list[i] = img_array
        print(img_list)
    
    return img_list

def train_test_split(data,random_seed=55,split=0.75):
    set_rdm = np.random.RandomState(seed=random_seed)
    dsize = len(data)
    ind = set_rdm.choice(dsize,dsize,replace=False)
    train_ind = ind[:int(0.75*dsize)]
    val_ind = ind[int(0.75*dsize):]
    return data[train_ind],data[val_ind]

def augment_pipeline(pipeline, images, seed=5):
    ia.seed(seed)
    processed_images = images.copy()
    for step in pipeline:
        temp = np.array(step.augment_images(images))
        processed_images = np.append(processed_images, temp, axis=0)
    return(processed_images)


full_train = load_image_from_dir('P:/2020/14/Kodning/Code/custodyproject/machine_learning/kaggle/input/working/train')
full_target = load_image_from_dir('P:/2020/14/Kodning/Code/custodyproject/machine_learning/kaggle/input/working/train_cleaned')


rotate90 = iaa.Rot90(1) # rotate image 90 degrees
rotate180 = iaa.Rot90(2) # rotate image 180 degrees
rotate270 = iaa.Rot90(3) # rotate image 270 degrees
random_rotate = iaa.Rot90((1,3)) # randomly rotate image from 90,180,270 degrees
perc_transform = iaa.PerspectiveTransform(scale=(0.02, 0.1)) # Skews and transform images without black bg
rotate10 = iaa.Affine(rotate=(10)) # rotate image 10 degrees
rotate10r = iaa.Affine(rotate=(-10)) # rotate image 30 degrees in reverse
crop = iaa.Crop(px=(5, 32)) # Crop between 5 to 32 pixels
hflip = iaa.Fliplr(1) # horizontal flips for 100% of images
vflip = iaa.Flipud(1) # vertical flips for 100% of images
gblur = iaa.GaussianBlur(sigma=(1, 1.5)) # gaussian blur images with a sigma of 1.0 to 1.5
motionblur = iaa.MotionBlur(8) # motion blur images with a kernel size 8

seq_rp = iaa.Sequential([
    iaa.Rot90((1,3)), # randomly rotate image from 90,180,270 degrees
    iaa.PerspectiveTransform(scale=(0.02, 0.1)) # Skews and transform images without black bg
])

seq_cfg = iaa.Sequential([
    iaa.Crop(px=(5, 32)), # crop images from each side by 5 to 32px (randomly chosen)
    iaa.Fliplr(0.5), # horizontally flip 50% of the images
    iaa.GaussianBlur(sigma=(0, 1.5)) # blur images with a sigma of 0 to 1.5
])

seq_fm = iaa.Sequential([
    iaa.Flipud(1), # vertical flips all the images
    iaa.MotionBlur(k=6) # motion blur images with a kernel size 6
])


pipeline = []
pipeline.append(rotate90)
pipeline.append(rotate180)
pipeline.append(rotate270)
pipeline.append(random_rotate)
pipeline.append(perc_transform)
pipeline.append(rotate10)
pipeline.append(rotate10r)
pipeline.append(crop)
pipeline.append(hflip)
pipeline.append(vflip)
pipeline.append(gblur)
pipeline.append(motionblur)
pipeline.append(seq_rp)
pipeline.append(seq_cfg)
pipeline.append(seq_fm)

processed_train = augment_pipeline(pipeline, full_train.reshape(-1,target_height,target_width))
processed_target = augment_pipeline(pipeline, full_target.reshape(-1,target_height,target_width))

processed_train = processed_train.reshape(-1,target_height,target_width,1)
processed_target = processed_target.reshape(-1,target_height,target_width,1)

print(processed_train.shape)


### Multi layer auto encoder with LeakyRelu and Normalization
input_layer = Input(shape=(None,None,1))

# encoder
e = Conv2D(32, (3, 3), padding='same')(input_layer)
e = LeakyReLU(alpha=0.3)(e)
e = BatchNormalization()(e)
e = Conv2D(64, (3, 3), padding='same')(e)
e = LeakyReLU(alpha=0.3)(e)
e = BatchNormalization()(e)
e = Conv2D(64, (3, 3), padding='same')(e)
e = LeakyReLU(alpha=0.3)(e)
e = MaxPooling2D((2, 2), padding='same')(e)

# decoder
d = Conv2D(64, (3, 3), padding='same')(e)
d = LeakyReLU(alpha=0.3)(d)
d = BatchNormalization()(d)

d = Conv2D(64, (3, 3), padding='same')(d)
d = LeakyReLU(alpha=0.3)(d)
# e = BatchNormalization()(e)
d = UpSampling2D((2, 2))(d)
d = Conv2D(32, (3, 3), padding='same')(d)
d = LeakyReLU(alpha=0.2)(d)
# d = Conv2D(128, (3, 3), padding='same')(d)
output_layer = Conv2D(1, (3, 3), activation='sigmoid', padding='same')(d)

# optimizer = Adam(lr=1e-4, decay=7e-6)
optimizer = Adam(lr=9e-4, decay=1e-5)
AEmodel = Model(input_layer,output_layer)
AEmodel.compile(loss='mse', optimizer=optimizer)
AEmodel.summary()

early_stopping = EarlyStopping(monitor='val_loss',
                               min_delta=0,
                               patience=10,
                               verbose=1, 
                               mode='auto')

checkpoint1 = ModelCheckpoint('best_val_loss.h5',
                             monitor='val_loss',
                             save_best_only=True)

checkpoint2 = ModelCheckpoint('best_loss.h5',
                             monitor='loss',
                             save_best_only=True)



history = AEmodel.fit(processed_train, processed_target,
                      batch_size=16, epochs=300, verbose=1,callbacks=[early_stopping, checkpoint2])


AEmodel.save('P:/2020/14/Kodning/Code/custodyproject/machine_learning/kaggle/AutoEncoderModelFull.h5')




    