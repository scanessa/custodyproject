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

