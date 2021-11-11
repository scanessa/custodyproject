# -*- coding: utf-8 -*-
"""
Created on Fri Nov  5 09:28:24 2021

@author: ifau-SteCa
"""
import os, pandas as pd
rootdir = "P:/2020/14/Tingsrätter"
pdf_files = []
output_path = r'P:/2020/14/Kodning/court_docs_register2.csv'

includes = 'all_cases'

data = {'file' : []}

for subdir, dirs, files in os.walk(rootdir, topdown=True):
    for file in files:
        if includes in subdir:
            pdf_dir = (os.path.join(subdir, file))
            data['file'].append(pdf_dir)
            continue

df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)
df.to_csv(output_path, mode = 'a', sep = ',', encoding='utf-8-sig')
       