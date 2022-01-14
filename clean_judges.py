# -*- coding: utf-8 -*-
"""
Created on Tue Jan  4 12:39:59 2022

@author: ifau-SteCa

Code to aims to:
    1: clean judge variable and return original dataframe without misspelled judges, reduces number of judge names
    2: output csv with judges x time and input list of courts to see which courts judges worked at at time t, where time is year, month
"""

from fuzzywuzzy import process
import pandas as pd
from collections import Counter

#Runtime
import time
start_time = time.time()

#Read in CSV created by domar_preprocessing.py
path = 'P:/2020/14/Data/Judges/judges_selection.csv'
#/Rulings/custody_data_allfiles.csv
#/Judges/judges_selection.csv
output_path  = 'P:/2020/14/Data/Judges/uniquejudges.csv'
datafr = pd.read_csv(path)
   
def condensed_df(df, keep_cols):
    df = df.rename(columns={
        "Tingsrätt": "court", 
        "År avslutat": "date",
        "Domare": "judge"
        })
    df = df[keep_cols]
    df['judge'] = df['judge'].str.strip()
    df = df.drop(df[(df['judge'] == 'error')].index)
    df = df.sort_values(by=['judge','court', 'date'])
    return df

#Replace judge names that occur only once per court with similar judge names, similar = 2 or less characters difference
def clean_judges(df, court, group_column_string, result_column_string):
    judges = []
    df2 = df.loc[df[group_column_string] == court] 
    for index, row in df2.iterrows():
        judges.append(row[result_column_string])
    singleJudges = [k for k, v in (Counter(judges)).items() if v == 1] 
    for currentJudge in singleJudges:
        nameLength = len(currentJudge)
        similarity = process.extract(currentJudge, judges)
        for i in similarity:
            ratio = i[1]/100
            changes = nameLength - (ratio * nameLength)
            if changes <= 2 and changes > 0:
                newJudge = i[0]
                df2[result_column_string] = df2[result_column_string].replace([currentJudge],newJudge)                            
    return df2

def clean_judges2(df):
    for index,row in df.iterrows():
        if row['last_appear'] == '1':
            first1 = row['firstname']
            court1 = row['court']
            judge1 = row['judge']
            year1 = row['year']
            month1 = int(row['month'])
            for index, row in (df[df['firstname'] == first1]).iterrows():
                year2 = row['year']
                month2 = int(row['month'])
                dist = month2 - month1
                court2 = row['court']
                judge2 = row['judge']
                if row['first_appear'] == '1' and year2 == year1 and dist <= 3 and court2 == court1 and judge2 != judge1:
                    df3.loc[index,'switch_name'] = court1
                if row['first_appear'] == '1' and dist < 6 and row['judge'] == judge1 and court1 != court2:
                    df3.loc[index,'change_court'] = court1
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

def first_last(df, group_by, ):
    df.loc[df.groupby(group_by).head(1).index, 'first_appear'] = '1'
    df.loc[df.groupby(group_by).tail(1).index, 'last_appear'] = '1'
    return df

def double_names(df, in_col_list ):
    df['double_names'] = df.duplicated(subset=in_col_list) 
    return df

def changed_name(df):
    for index,row in df.iterrows():
        if row['last_appear'] == '1':
            first1 = row['firstname']
            court1 = row['court']
            judge1 = row['judge']
            year1 = row['year']
            month1 = int(row['month'])
            for index, row in (df[df['firstname'] == first1]).iterrows():
                year2 = row['year']
                month2 = int(row['month'])
                dist = month2 - month1
                court2 = row['court']
                judge2 = row['judge']
                if row['first_appear'] == '1' and year2 == year1 and dist <= 3 and court2 == court1 and judge2 != judge1:
                    df3.loc[index,'switch_name'] = court1
                if row['first_appear'] == '1' and dist < 6 and row['judge'] == judge1 and court1 != court2:
                    df3.loc[index,'change_court'] = court1
    return df
 
#Execute
condensed = condensed_df(datafr, ['court','judge','date'])
all_courts, first_court, remaining_courts = unique_items(condensed, 'court')
base_df = clean_judges(condensed, first_court, 'court','judge')
for court in remaining_courts:
    new_df = clean_judges(condensed, court, 'court','judge')
    base_df = append_dfs(base_df, new_df)

#Output list tracking judges
base_df['month'], base_df['year'] = add_column(base_df, 'date', '-', 1),  add_column(base_df, 'date', '-', 0) 
base_df['firstname'], base_df['lastname'] = add_column(base_df, 'judge', ' ', 0), add_column(base_df, 'judge', ' ', -1) 
df3 = base_df.drop_duplicates(subset=(['judge','court','month','year']))

double_names(df3, ['judge','month','year'])
first_last(df3, ['court','judge'])
changed_name(df3)

#Do change name fo hyphenated name
#Years within court

#Print
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print('\nNew DF\n',df3)
#df3.to_csv(output_path, sep = ',', encoding='utf-8-sig')
    
#Runtime    
print("\nRuntime: \n" + "--- %s seconds ---" % (time.time() - start_time))




