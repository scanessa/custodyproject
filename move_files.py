# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 14:49:04 2022

@author: ifau-SteCa
"""
import shutil
import pathlib
import os.path
import re
import glob
import random

filepaths_doc = 'P:/2020/14/Kodning/Clean_csvs_move_files/filepaths.txt' 
includes = ''
ROOTDIR = 'P:/2020/14/Tingsratter/'
INCLUDES = ["phone", "all_scans"]
DESTINATION = "P:/2020/14/Kodning/Scans/all_scans/others/new"

error_paths = [] 

def searchKey(string, part):
    finder = re.compile(string)
    match = finder.search(part)
    return match

def read_filepaths(doc):
    with open(doc,'r') as f:
        paths = f.read().splitlines() 
    return paths

def move_files(paths, error_files, pdf_dir):
    errors = 0
    for file in paths:
        p = pathlib.PureWindowsPath(file)
        p = str(p.as_posix())
        print(p)
        try:
            shutil.move(file,pdf_dir)
        except:
            errors += 1
            error_files.append(file)
    
    print('%d files threw an error: ' %(errors), error_paths)
    return errors, error_files

def copy_files(paths, pdf_dir):
    errors = 0
    for file in paths:
        p = pathlib.PureWindowsPath(file)
        p = str(p.as_posix())
        try:
            shutil.copy(file,pdf_dir)
        except:
            errors += 1
            print("Error: ",p)
    
    print('%d files threw an error' %(errors))
    return errors

def true_file(files):
    for fname in files:
        if not os.path.isfile(fname):
            print('N: ', fname)
            
def file_counter(path, searchkey):
    fileCount = len(glob.glob1(path,searchkey))   
    return fileCount
         
def newname(rootdir):
    """
    Rename scanned files bc () throw an error with OCR
    Rename only files that are not in the new name pattern: COURT0, COURT1, ...
    Remove comment for second court definition if court is not folder name
    """
    for subdir, dirs, files in os.walk(rootdir, topdown=True):
        court = subdir.split('/')[4]
        court = 'Sodertorns'
        existing = file_counter(subdir, court + '*')
        for file in files:
            counter = str(existing)
            if includes in subdir and file.endswith('.JPG') and not searchKey(court+'\d',file):
                file_new = court + counter + '.JPG'
                print('OLD: ', os.path.join(subdir, file))
                print('NEW: ', os.path.join(subdir, file_new))
                os.rename(os.path.join(subdir, file), os.path.join(subdir, file_new))
                existing += 1
                
def changename(rootdir):
    """
    Remove () from filename
    """
    for subdir, dirs, files in os.walk(rootdir, topdown=True):
        for file in files:
            if includes in subdir and file.endswith('.JPG'):
                file_new = file.replace("(","_").replace(")","").replace(" ","_").replace("ä","a").replace("ö","o").replace("ü","u").replace("å","a")
                print('OLD: ', os.path.join(subdir, file))
                print('NEW: ', os.path.join(subdir, file_new))
                os.rename(os.path.join(subdir, file), os.path.join(subdir, file_new))



def randomsample(rootdir, destination):
    for rootdir, dirs, files in os.walk(rootdir):
        for subdir in dirs:
            dirpath = os.path.join(rootdir, subdir)
            if (
                    "phone" in dirpath
                    and not "1. Gemensamma dokument" in dirpath
                    or "all_scans" in dirpath
                    and not "1. Gemensamma dokument" in dirpath
                    
                ):
                
                allfiles = [x for x in os.listdir(dirpath) if not any(term in x.lower() for term in ["aktbil","dagbok","beslut"])]
                
                if len(allfiles) > 4:
                    filenames = random.sample(allfiles, 4)
                    filenames = [os.path.join(dirpath, x) for x in filenames]
                    copy_files(filenames, DESTINATION)

randomsample(ROOTDIR, DESTINATION)
