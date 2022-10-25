# -*- coding: utf-8 -*-
"""
Created on Tue Jan  4 12:39:59 2022

@author: ifau-SteCa

Code to aims to:
    1: clean judge variable and return original dataframe without misspelled judges, reduces number of judge names
    2: output csv with judges x time and input list of courts to see which courts judges worked at at time t, where time is year, month
"""


from fuzzywuzzy import fuzz
import pandas as pd
from datetime import date
import glob
import cv2
import pytesseract

# For importing custodydata module, launch python from within Code/custodyproject folder
import sys
sys.path.append('P:/2020/14/Kodning/Code/custodyproject/')


#Runtime
import time
start_time = time.time()

#Read in CSV created by domar_preprocessing.py
output_path  = "P:/2020/14/Kodning/Test-round-5-Anna/rulings_data_altjudges.csv"


def condensed_df(df, keep_cols):
    df = df.rename(columns={
        "case_no": "case"
        })
    df = df[keep_cols]
    df['judge'] = df['judge'].str.strip()
    df = df.drop(df[(df['judge'] == 'error')].index)
    df = df.drop(df[(df['judge'] == 'övrigt')].index)
    df = df[df['date'].notnull()]
    df = df.drop_duplicates(subset=(['court','case', 'date']))
    df = df.sort_values(by=['judge','court', 'date'])
    return df

def clean_judge_names(df):
    df['occurances'] = df.groupby('judge')['court'].transform('size')
    for index1,row in df.iterrows():
        if row['occurances'] <= 5:
            court1 = row['court']
            judge1 = row['judge']
            for index2, row in (df[df['court'] == court1]).iterrows():
                judge2 = row['judge']
                similarity = fuzz.ratio(judge1,judge2)
                contained = fuzz.partial_ratio(judge1, judge2)
                if 80 < similarity < 100 or contained == 100 and judge1 != judge2:
                    df.loc[index1,'judge_old'] = judge1
                    df.loc[index1,'judge'] = judge2
    return df

def partial_names(df):
    distinct_judges = pd.Series(df['judge']).unique()
    for index1,row in df.iterrows():
        judge1 = row['judge']
        for i in distinct_judges:
            tokenmatch = fuzz.token_set_ratio(i, judge1)
            if tokenmatch == 100 and i != judge1:
                df.loc[index1,'judge_old_token'] = i
    return df


def append_dfs(df_old, df_new):
    df1 = df_old.append(df_new, ignore_index = True)
    return df1

def unique_items(df, column):
    diction = df.to_dict('series')
    long_list = diction[column]
    short_list = pd.Series(long_list).unique()
    first_item = short_list[0]
    remaining_items = short_list[1:]
    return short_list, first_item, remaining_items

def add_column(df,var_string, char_string, split):
    split_on_char = df[var_string].map(lambda x: x.split(char_string)[split])
    return split_on_char

def first_last(df, group_by):
    df.loc[df.groupby(group_by).head(1).index, 'first_appear'] = '1'
    df.loc[df.groupby(group_by).tail(1).index, 'last_appear'] = '1'
    return df

def double_names(df, in_col_list ):
    df['double_names'] = df.duplicated(subset=in_col_list) 
    #would be nice to have the court where the double occurs instead of true/false
    #only if judge in other court tries more than 1 case
    return df

def changed_name(df):
    for index1,row in df.iterrows():
        if row['last_appear'] == '1':
            first1 = row['firstname']
            court1 = row['court']
            judge1 = row['judge']
            try:
                date1 = date.fromisoformat(row['date'])
            except ValueError:
                break
            for index2, row in (df[df['firstname'] == first1]).iterrows():
                try:
                    date2 = date.fromisoformat(row['date'])
                except ValueError:
                    break
                delta = date2-date1
                court2 = row['court']
                judge2 = row['judge']
                if row['first_appear'] == '1' and 0 < delta.days < 60 and judge2 != judge1:
                    df.loc[index1,'switch_name'] = judge1
                if row['first_appear'] == '1' and date2>date1 and judge2 == judge1 and court1 != court2:
                    df.loc[index1,'change_court'] = court2
    return df



def main_clean_digital():
    path = 'P:/2020/14/Data/Rulings/custody_data_allfiles.csv'
    datafr = pd.read_csv(path)

    condensed = condensed_df(datafr, ['court','judge','date', 'case'])
    print('Runtime so far: ', (time.time() - start_time))
    base_df = clean_judge_names(condensed)
    print('Runtime so far: ', (time.time() - start_time))
    base_df['month'], base_df['year'] = add_column(base_df, 'date', '-', 1),  add_column(base_df, 'date', '-', 0) 
    base_df['firstname'], base_df['lastname'] = add_column(base_df, 'judge', ' ', 0), add_column(base_df, 'judge', ' ', -1)
    print('Runtime so far: ', (time.time() - start_time))
    df3 = base_df.drop_duplicates(subset=(['judge','court','month','year']))
    print('Runtime so far: ', (time.time() - start_time))
    double_names(df3, ['judge','month','year'])
    print('Runtime so far: ', (time.time() - start_time))
    first_last(df3, ['court','judge'])
    changed_name(df3)
    print('Runtime so far: ', (time.time() - start_time))
    #partial_names(df3)
    
    #Print
    with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
        print('\nNew DF\n',df3)
    df3.to_csv(output_path, sep = ',', encoding='utf-8-sig')


"""
Find existing judge names in noisy judge names from scans
"""
def import_judges(path):
    data = pd.read_csv(path)
    data = data['judge'].values
    
    return list(data)

def clean_names(lst):
    lst = [x for x in lst if not "tingsr" in x]
    lst = [x for x in lst if not " dom " in x]
    lst = [x for x in lst if not " sid " in x]
    lst = [' '.join(list(set(name.split()))) for name in lst]
    lst = list(set(lst))

    return lst

def compare_name(df, lst):
    for index,row in df.iterrows():
        altern_j = []
        noisy_j = row['judge']

        for clean_j in lst:
            
            try:
                contain = fuzz.partial_ratio(noisy_j, clean_j)
            except:
                pass

            if contain > 90 and noisy_j != clean_j:
                altern_j.append(clean_j)
        if len(altern_j) < 3:
            altern_j = ",". join(altern_j)
            df.loc[index,'alternative_names'] = altern_j
        
    return df
            
    
    
def clean_scanned_judges():
    j_scans = import_judges("P:/2020/14/Data/Judges/scan_judges_10plus_cases.csv")
    j_digital = import_judges("P:/2020/14/Data/Judges/digital_judges_10plus_cases.csv")
    j_comb= j_scans + j_digital
    
    j_comb = clean_names(j_comb)
    scans = pd.read_csv("P:/2020/14/Kodning/Test-round-5-Anna/rulings_data_AH_100_v2.csv")
    print("Comparing names...")
    scans = compare_name(scans, j_comb)
    scans.to_csv(output_path, sep = ',', encoding='utf-8-sig')
    print("Saved")

if __name__ == '__main__':
    clean_scanned_judges()    
    
    #Runtime    
    print("\nRuntime: \n" + "--- %s seconds ---" % (time.time() - start_time))




