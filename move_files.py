# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 14:49:04 2022

@author: ifau-SteCa
"""
import shutil, pathlib, os.path

pdf_dir = 'P:/2020/14/Kodning/Test-round-4/check4/subcheck/notdone'
filepaths_doc = 'P:/2020/14/Kodning/Test-round-4/check4/subcheck/filepaths.txt' 
noCopy = 0 
error_paths = []  

def read_filepaths(doc):
    with open(doc,'r') as f:
        paths = f.read().splitlines() 
    return paths

def copy_files(paths, errors, error_files):        
    for file in paths:
        p = pathlib.PureWindowsPath(file)
        p = str(p.as_posix())
        print(p)
        try:
            shutil.copy(file,pdf_dir)
        except:
            errors += 1
            error_files.append(file)
            continue
    return errors, error_files

def true_file(files):
    for fname in files:
        if not os.path.isfile(fname):
            print('N: ', fname)
            
#Execute
sample = read_filepaths(filepaths_doc)
copy_files(sample, noCopy, error_paths)

#Output
print('%d files threw an error: ' %(noCopy), error_paths)