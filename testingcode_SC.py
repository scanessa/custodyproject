# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 10:20:43 2021

@author: ifau-SteCa
"""
import re, io, glob, os, fnmatch, pandas as pd 

rootdir = "P:/2020/14/Tingsrätter/ÖÖ_Case_Sorting_SC"
output_path = r'P:/2020/14/Kodning/court_docs_register.csv'
pdf_files = []

includes = 'all_cases'
for subdir, dirs, files in os.walk(rootdir, topdown=True):
    for file in files:
        if includes in subdir:
            pdf_dir = (os.path.join(subdir, file))
            pdf_files.append(pdf_dir)
            continue
        
print(pdf_files)