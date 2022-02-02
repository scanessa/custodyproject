# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 14:49:04 2022

@author: ifau-SteCa
"""
import shutil, pathlib

pdf_dir = 'P:/2020/14/Kodning/Test-round-4/check4/subcheck/notdone'
filepaths_doc = 'P:/2020/14/Kodning/Test-round-4/check4/subcheck/filepaths.txt'

noCopy = 0 
error_files = []  

with open(filepaths_doc,'r') as f:
    sample_files = f.read().splitlines() 
    
for file in sample_files:
    p = pathlib.PureWindowsPath(file)
    p = str(p.as_posix())
    print(p)
    try:
        shutil.copy(file,pdf_dir)
    except:
        noCopy += 1
        error_files.append(file)
        continue

print(noCopy)
print('Files that could not be copied: ', error_files)