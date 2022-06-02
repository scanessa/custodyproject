"""
Clustering images into similar groups
Taken from: https://towardsdatascience.com/how-to-cluster-images-based-on-visual-similarity-cd6e7209fe34
Author: Gabe Flomo

Determine k: https://www.geeksforgeeks.org/ml-determine-the-optimal-value-of-k-in-k-means-clustering/#:%7E:text=There%20is%20a%20popular%20method,fewer%20elements%20in%20the%20cluster

Instructions:
    - Move all signature files to path folder
    - Run code only until DETERMINE K: Determine number of clusters (K); number of clusters should be most notable dip in plot
    - Once determined K, run full code to get clusters
    
TO DO:
    Try different clustering methods (see options here: https://scikit-learn.org/stable/auto_examples/cluster/plot_cluster_comparison.html)
    Guessing the K for k-means in a sample like this, where the groups are not very nicely seperated, is quite imprecise
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

# for everything else
import os
import numpy as np
import matplotlib.pyplot as plt
import pickle
from sklearn.cluster import KMeans

PATH = r"P:/2020/14/Kodning/Scans/all_scans/100signatures/"
FILE_ENDING = '.jpg'

path = PATH
# change the working directory to the path where the images are located
os.chdir(path)

# this list holds all the image filename
flowers = []

# creates a ScandirIterator aliased as files
with os.scandir(path) as files:
  # loops through each file in the directory
    for file in files:
        if file.name.endswith(FILE_ENDING):
          # adds only the image files to the flowers list
            flowers.append(file.name)

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
   
data = {}
p = PATH

# lop through each image in the dataset
for flower in flowers:
    # try to extract the features and update the dictionary
    try:
        feat = extract_features(flower,model)
        data[flower] = feat
    # if something fails, save the extracted features as a pickle file (optional)
    except:
        with open(p,'wb') as file:
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

"""
DETERMINE K
"""

inertia = []
distortions =  []
mapping1 = {}
mapping2 = {}

list_k = list(range(3, 50))

for k in list_k:
    km = KMeans(n_clusters=k, random_state=22)
    km.fit(X)
    distortions.append(sum(np.min(cdist(X, km.cluster_centers_,
                                        'euclidean'), axis=1)) / X.shape[0])
    inertia.append(km.inertia_)
    
    mapping1[k] = sum(np.min(cdist(X, km.cluster_centers_,
                                   'euclidean'), axis=1)) / X.shape[0]
    mapping2[k] = km.inertia_

# Plot sse against k
plt.figure(figsize=(6, 6))
plt.plot(list_k, inertia)
plt.xlabel(r'Number of clusters *k*')
plt.ylabel('Sum of squared distance');

print("Mapping 2:\n")
for key, val in mapping2.items():
	print(f'{key} : {val}')


SELECTED_K = 32

"""
CLUSTER
"""

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



