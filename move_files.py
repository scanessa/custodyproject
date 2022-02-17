# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 14:49:04 2022

@author: ifau-SteCa
"""
import shutil, pathlib, os.path

#pdf_dir = "P:/2020/14/Tingsrätter/"
filepaths_doc = 'P:/2020/14/Kodning/Clean_csvs_move_files/filepaths.txt' 
includes = 'Test'

noCopy = 0 
i = 0
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
            
def rename_file(rootdir):
    i = 0
    for subdir, dirs, files in os.walk(rootdir, topdown=True):
        court = subdir.split('/')[4]
        for file in files:
            counter = str(i)
            if includes in subdir and file.endswith('.pdf'):
                file_new = court + counter + '.pdf'
                os.rename(os.path.join(rootdir, file), os.path.join(rootdir, file_new))
                i += 1
                continue

#Execute
#sample = read_filepaths(filepaths_doc)
#copy_files(sample, noCopy, error_paths)
#rename_file(pdf_dir)

#Output
print('%d files threw an error: ' %(noCopy), error_paths)