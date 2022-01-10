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

#Instead of making dataframe, take dataframe that is output by domar_preprocessing.py
#REPLACING MARKUS WITH JOHNESS DOESNT WORK BECUASE JOHANNES THEN TURNS INTO ANNE 
courts = ['a', 'b']
data = {'court':['a','a','a','a','a','b'], 
        'judge':['jon doe','jon doe','jon doe','jon smith','jon smith','jon smith'],
        'outcome':['1','2','3','4','5','6'],
        'date': ['2000-01-01','2001-02-01','2001-01-01','2001-03-01','2002-01-01','2002-01-01']
        }
test = pd.DataFrame(data)

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
    
#Execute
all_courts, first_court, remaining_courts = unique_items(test, 'court')
base_df = clean_judges(test, first_court, 'court','judge')
for court in remaining_courts:
    new_df = clean_judges(test, court, 'court','judge')
    base_df = append_dfs(base_df, new_df)

#Output list tracking judges

selected_columns = base_df[['judge','court','date']]
df1 = selected_columns.copy()
df1['month'] = df1['date'].map(lambda x: int(x.split('-')[1]))
df1['year'] = df1['date'].map(lambda x: int(x.split('-')[0]))
df3 = df1.drop_duplicates(subset=(['judge','court','month','year']))

#Judges with same name in different courts (different people)
df3['double_names'] = df3.duplicated(subset=['judge','month','year']) 
   
#Judges with new name in same court (same person)
df3['firstname'] = df3['judge'].map(lambda x: x.split()[0])
df3['lastname'] = df3['judge'].map(lambda x: x.split()[1])
df4 = df3.sort_values(by=['court','year', 'month'])
df4.loc[df4.groupby('judge').head(1).index, 'first_appear'] = '1'
df4.loc[df4.groupby('judge').tail(1).index, 'last_appear'] = '1'

"""
now put first, last, month, year in a dict, for each last that appears
new and has the same first name as a last that disappears we assume
the person changed their name

OR

iterate over all last names that disappear, for each see if the first name
occurs among the first names that appear, within the same court
potential next step: check for double name, if old disappearing name 
occurs in new appearing name its a double name 
"""



"""
look at first and last name within court, if a last name disappears and the 
same first name appears the next month with a different last name, and the 
original last name/first name combination did not appear in a different court 
(switching courts) we can assume a judge changed names
"""

print('Original DF\n', base_df)
print('\nNew DF\n', df4)

