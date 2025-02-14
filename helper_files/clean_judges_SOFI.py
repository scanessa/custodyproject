# -*- coding: utf-8 -*-
"""
Created on Tue Jan  4 12:39:59 2022

@author: ifau-SteCa

Code to aims to:
    1: clean judge variable and return original dataframe without misspelled judges, reduces number of judge names
    2: output csv with judges x time and input list of courts to see which courts judges worked at at time t, where time is year, month
"""
import pandas as pd
import gender_guesser.detector as gender
gend = gender.Detector(case_sensitive=False)

import time
start_time = time.time()

def get_judge_gender(path):
    """
    Input csv list of judges and attached merge id
    """
    df = pd.read_csv(path)
    for index,row in df.iterrows():

        if isinstance(row['judge'], str):
            judge_first = row['judge'].replace("-", " ").split()[0]
        else:
            judge_first = "-"
        
        judge_gend = gend.get_gender(judge_first)
        df.loc[index,'judge_gender'] = judge_gend
        
    df.to_csv(path.replace(".csv", "_done.csv"), sep = ',', encoding='utf-8-sig')


if __name__ == '__main__':
    get_judge_gender("PATH/judge_list_for_judge_gender.csv")   
    
    #Runtime    
    print("\nRuntime: \n" + "--- %s seconds ---" % (time.time() - start_time))




