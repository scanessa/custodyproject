from appendix_classification import predict
import os
import glob

for file in glob.glob("P:/2020/14/Kodning/Scans/ML_appendix/test_small/*.jpg"):
    res = predict(file)
    if res == 1:
        newname = file.split('.jpg')[0] + '_appendix.jpg'
        os.rename(file, newname)
        print(file,newname)
        


