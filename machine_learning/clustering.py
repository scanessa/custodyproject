"""
Clustering images into similar groups based on autoencoders and k-means
Sources:
Simple k-means: https://towardsdatascience.com/how-to-cluster-images-based-on-visual-similarity-cd6e7209fe34
Determine k: https://www.geeksforgeeks.org/ml-determine-the-optimal-value-of-k-in-k-means-clustering/#:%7E:text=There%20is%20a%20popular%20method,fewer%20elements%20in%20the%20cluster

Autoencoder: https://minimatech.org/autoencoder-with-manifold-learning-for-clustering-in-python/
    
"""

# for loading/processing the images  
from keras.preprocessing.image import load_img 
from keras.applications.vgg16 import preprocess_input 

# models 
from keras.applications.vgg16 import VGG16 
from keras.models import Model

# clustering and dimension reduction
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from keras.models import Model
from keras.layers import Dense, Input
from keras.preprocessing import sequence
from sklearn.model_selection import train_test_split
from sklearn.cluster import DBSCAN
from sklearn.manifold import Isomap

# for everything else
import os
import numpy as np
import matplotlib.pyplot as plt
import pickle
import umap.umap_ as umap
import seaborn as sns


PATH = r"P:/2020/14/Kodning/Scans/all_scans/100signatures/signatures/"
FILE_ENDING = '.jpg'
data = {}

path = PATH
# change the working directory to the path where the images are located
os.chdir(path)

# this list holds all the image filename
signs = []

# creates a ScandirIterator aliased as files
with os.scandir(path) as files:
  # loops through each file in the directory
    for file in files:
        if file.name.endswith(FILE_ENDING):
          # adds only the image files to the flowers list
            signs.append(file.name)

model = VGG16()
model = Model(inputs = model.inputs, outputs = model.layers[-2].output)

def extract_features(file, model):
    # load the image as a 224x224 array
    img = load_img(file, target_size=(224,224))
    # convert from 'PIL.Image.Image' to numpy array
    img = np.array(img) 
    # reshape the data for the model reshape(num_of_samples, dim 1, dim 2, channels)
    reshaped_img = img.reshape(1,224,224,3) 
    # prepare image for model
    imgx = preprocess_input(reshaped_img)
    # get the feature vector
    features = model.predict(imgx, use_multiprocessing=True)
    return features
   
# lop through each image in the dataset
for sign in signs:
    # try to extract the features and update the dictionary
    try:
        feat = extract_features(sign,model)
        data[sign] = feat
    # if something fails, save the extracted features as a pickle file (optional)
    except:
        with open(PATH,'wb') as file:
            pickle.dump(data,file)
          
 
# get a list of the filenames
filenames = np.array(list(data.keys()))

# get a list of just the features
feat = np.array(list(data.values()))

# reshape so that there are 210 samples of 4096 vectors
feat = feat.reshape(-1,4096)

# reduce the amount of dimensions in the feature vector
pca = PCA(n_components=100, random_state=22)
pca.fit(feat)
X = pca.transform(feat)

X_train, X_rem, y_train, y_rem = train_test_split(X, X, train_size=0.8)
X_valid, X_test, y_valid, y_test = train_test_split(X_rem,y_rem, test_size=0.5)

max_len = 500
X_train = sequence.pad_sequences(X_train, maxlen = max_len)
X_test = sequence.pad_sequences(X_test, maxlen = max_len)

## define the encoder
inputs_dim = X_train.shape[1]
encoder = Input(shape = (inputs_dim, ))
e = Dense(1024, activation = "relu")(encoder)
e = Dense(512, activation = "relu")(e)
e = Dense(256, activation = "relu")(e)


## bottleneck layer
n_bottleneck = 10
## defining it with a name to extract it later
bottleneck_layer = "bottleneck_layer"
# can also be defined with an activation function, relu for instance
bottleneck = Dense(n_bottleneck, name = bottleneck_layer)(e)

## define the decoder (in reverse)
decoder = Dense(256, activation = "relu")(bottleneck)
decoder = Dense(512, activation = "relu")(decoder)
decoder = Dense(1024, activation = "relu")(decoder)


## output layer
output = Dense(inputs_dim)(decoder)
## model
model = Model(inputs = encoder, outputs = output)
model.summary()

# Model: "model"
# _________________________________________________________________
# Layer (type) Output Shape Param #
# =================================================================
# input_2 (InputLayer) [(None, 500)] 0
# _________________________________________________________________
# dense_14 (Dense) (None, 1024) 513024
# _________________________________________________________________
# dense_15 (Dense) (None, 512) 524800
# _________________________________________________________________
# dense_16 (Dense) (None, 256) 131328
# _________________________________________________________________
# bottleneck_layer (Dense) (None, 10) 2570
# _________________________________________________________________
# dense_17 (Dense) (None, 256) 2816
# _________________________________________________________________
# dense_18 (Dense) (None, 512) 131584
# _________________________________________________________________
# dense_19 (Dense) (None, 1024) 525312
# _________________________________________________________________
# dense_20 (Dense) (None, 500) 512500
# =================================================================
# Total params: 2,343,934
# Trainable params: 2,343,934
# Non-trainable params: 0
# _________________________________________________________________


## extracting the bottleneck layer we are interested in the most
## in case you haven't defined it as a layer on it own you can extract it by name 
#bottleneck_encoded_layer = model.get_layer(name = bottleneck_layer).output
## the model to be used after training the autoencoder to refine the data
#encoder = Model(inputs = model.input, outputs = bottleneck_encoded_layer)
# in case you defined it as a layer as we did
encoder = Model(inputs = model.input, outputs = bottleneck)

model.compile(loss = "mse", optimizer = "adam")

history = model.fit(
    X_train,
    X_train,
    batch_size = 32,
    epochs = 25,
    verbose = 1,
    validation_data = (X_test, X_test)
)

# Epoch 1/25
# 782/782 [==============================] - 8s 9ms/step - loss: 0.0232 - val_loss: 0.0205
# ...
# ...
# Epoch 25/25
# 782/782 [==============================] - 6s 8ms/step - loss: 0.0152 - val_loss: 0.0176

history_dict = history.history
loss_values = history_dict["loss"]
val_loss_values = history_dict["val_loss"]
epochs = range(25)
plt.plot(epochs, loss_values, "bo", label = "training loss")
plt.plot(epochs, val_loss_values, "b", label = "validation loss")
plt.title("Training & validation loss")
plt.xlabel("epoch")
plt.ylabel("loss")
plt.legend()
plt.show()
# plt.clf() # to clear

## representing the data in lower dimensional representation or embedding
review_encoded = encoder.predict(X_train)
review_encoded.shape
# (25000, 10)

## install umap library use
# pip install umap-learn

review_umapped = umap.UMAP(n_components = n_bottleneck / 2, 
                           metric = "euclidean",
                           n_neighbors = 50, 
                           min_dist = 0.0,
                           random_state = 13).fit_transform(review_encoded)
review_umapped.shape
# (25000, 5)

np.random.seed(13)

review_isomapped = Isomap(n_components = n_bottleneck / 2,
                          n_neighbors = 50,
                          metric = "euclidean").fit_transform(review_encoded)

np.random.seed(13)

clusters = DBSCAN(
    min_samples = 50,
    eps = 1
).fit_predict(review_umapped)
len(set(clusters))
# 5


tsne2 = TSNE(2, metric = "euclidean", random_state = 13).fit_transform(review_encoded)

sns.scatterplot(tsne2[:, 0], tsne2[:, 1], 
                hue = clusters, palette = "deep",
                alpha = 0.9, s = 1,
                legend = "full")

kmeans2 = KMeans(n_clusters = 5, random_state = 13).fit_predict(review_umapped)
plt.scatter(tsne2[:, 0], tsne2[:, 1], c = kmeans2, s = 1) 
plt.show()

kmeans3 = KMeans(n_clusters = 5, random_state = 13).fit_predict(review_encoded)
plt.scatter(tsne2[:, 0], tsne2[:, 1], c = kmeans3, s = 1) 
plt.show()






"""
CLUSTER


cluster = KMeans(n_clusters=SELECTED_K, random_state=22)
cluster.fit(X)

# holds the cluster id and the images { id: [images] }
groups = {}
for file, cl in zip(filenames,cluster.labels_):
    if cl not in groups.keys():
        groups[cl] = []
        groups[cl].append(file)
    else:
        groups[cl].append(file)

# function that lets you view a cluster (based on identifier)        
def view_cluster(cluster):
    plt.figure(figsize = (25,25));
    # gets the list of filenames for a cluster
    files = groups[cluster]
    # only allow up to 30 images to be shown at a time
    if len(files) > 30:
        print(f"Clipping cluster size from {len(files)} to 30")
        files = files[:29]
    # plot each image in the cluster
    for index, file in enumerate(files):
        plt.subplot(10,10,index+1);
        img = load_img(file)
        img = np.array(img)
        plt.imshow(img)
        plt.axis('off')
        

for group in groups:
    for file in groups[group]:
        print(group, file)
        os.rename(file, str(group) + "_" + file)

"""

