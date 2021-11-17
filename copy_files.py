# -*- coding: utf-8 -*-
"""
Created on Tue Nov 16 14:01:10 2021

@author: ifau-SteCa
"""
import shutil
sample_files = []
pdf_dir =  "P:/2020/14/Tingsrätter/ÖÖ_Case_Sorting_SC/Domar/all_cases/Check2"

sample_files = ["P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/dagboksblad 2585-12.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2589-98.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 259-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2540-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2592-97.pdf",	"P:/2020/14/Tingsrätter/Vänersborg/Domar/all_cases/Vänersborgs TR T 2594-18 Aktbil 16.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2596-01.pdf",	"P:/2020/14/Tingsrätter/Uddevalla/Domar/all_cases/Uddevalla TR T 2599-20 Dagboksblad 2021-11-02.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/260-00.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/260-06.pdf",	"P:/2020/14/Tingsrätter/Alingsås/Domar/all_cases/Alingsås TR T 260-15 Dagboksblad 2021-06-29.pdf",	"P:/2020/14/Tingsrätter/Norrköping/Domar/all_cases/Norrköpings TR T 260-16 Aktbil 6.pdf",	"P:/2020/14/Tingsrätter/Nacka/Domar/all_cases/2600-07 dagbok.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/T 2601-07.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2601-14 Aktbil 31.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2602-06.pdf",	"P:/2020/14/Tingsrätter/Nyköping/Domar/all_cases/Nyköpings TR T 2603-15 Dagboksblad 2021-07-02.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_103541.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2605-99.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2608-07.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_101951.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2609-07.pdf",	"P:/2020/14/Tingsrätter/Solna/Domar/all_cases/2611-07.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_113825.pdf",	"P:/2020/14/Tingsrätter/Örebro/Domar/all_cases/2616-05.pdf",	"P:/2020/14/Tingsrätter/Umeå/Domar/all_cases/T 262-00.pdf",	"P:/2020/14/Tingsrätter/Gävle/Domar/all_cases/210929_114021.pdf",	"P:/2020/14/Tingsrätter/Eksjö/Domar/all_cases/Eksjö TR T 263-12 Dagboksblad 2021-06-22.pdf",	"P:/2020/14/Tingsrätter/Halmstad/Domar/all_cases/Halmstads TR T 2632-20 Dagboksblad 2021-09-22.pdf"]
    
for file in sample_files:
    shutil.copy(file,pdf_dir)
