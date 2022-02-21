# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 14:49:04 2022

@author: ifau-SteCa
"""
import shutil, pathlib, os.path, re, glob

pdf_dir = "P:/2020/14/Tingsrätter/Stockholms/Domar/all_scans/Test"
filepaths_doc = 'P:/2020/14/Kodning/Clean_csvs_move_files/filepaths.txt' 
includes = 'Test'

noCopy = 0 
i = 0
error_paths = [] 

def searchKey(string, part):
    finder = re.compile(string)
    match = finder.search(part)
    return match

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
            
def file_counter(path, searchkey):
    fileCount = len(glob.glob1(path,searchkey))   
    return fileCount
         
def rename_file(rootdir):
    for subdir, dirs, files in os.walk(rootdir, topdown=True):
        court = subdir.split('/')[4]
        existing = file_counter(subdir, court + '*')
        for file in files:
            counter = str(existing)
            if includes in subdir and file.endswith('.pdf') and not searchKey(court+'\d',file):
                file_new = court + counter + '.pdf'
                os.rename(os.path.join(rootdir, file), os.path.join(rootdir, file_new))
                existing += 1
                continue

#Execute
#sample = read_filepaths(filepaths_doc)
#copy_files(sample, noCopy, error_paths)
rename_file(pdf_dir)

#Output
print('%d files threw an error: ' %(noCopy), error_paths)