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
courts = ['a', 'b']
data = {'court':['a','a','a','a','a','a','b','b','b','a'], 
        'judge':['anna','anne','anna','jaja muller','jojo muller','jojo muller','kurt','jona','jona','jona',],
        'outcome':['1','2','3','4','5','6','7','8','9','10'],
        'date': ['2000-01-31','2000-02-01','2001-01-01','2001-05-01','2001-05-17','2000-01-01','2000-01-01','2007-01-01','2008-01-21','2008-01-01']
        }
test = pd.DataFrame(data)

#Replace judge names that occur only once per court with similar judge names, similar = 2 or less characters difference
def clean_judges(df, court_list, group_column_string, result_column_string):
    for court in court_list:  
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
                if changes <= 2:
                    newJudge = i[0]
                    df[result_column_string] = df[result_column_string].replace([currentJudge],newJudge)
    return df

#Output list tracking judges
selected_columns = test[['court','judge','date']]
judges_df = selected_columns.copy()

print(test)
print(judges_df)

"""
#Execute
print('Old\n', test)
clean_judges(test, courts, 'court','judge')
print('\nNew\n',test)
"""
