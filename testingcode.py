import os
import glob
import time
from collections import defaultdict

path = "P:/2020/14/Kodning/Scans/all_scans/"
os.chdir(path)

start = time.time()


group_dict = defaultdict(list)
for fn in glob.glob("*.txt"):
    
    print(fn)
    
    text = open(fn, "r")
    full_text = text.read()
    full_text = full_text.split('__newpage__')
    full_text = [x for x in full_text if not x == '\n']
    print(full_text)
