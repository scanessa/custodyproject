# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 09:06:04 2022

@author: ifau-SteCa
"""
s=[["a","b","c"]]
flat_list = [item for sublist in s for item in sublist]

a = [x for x in flat_list if "b" in x]

print(a)