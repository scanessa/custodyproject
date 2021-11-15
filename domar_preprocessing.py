# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 17:50:55 2021

@author: ifau-SteCa


Purpose of the code is to read in all pdfs from a specified folder path, extract information (child ID, case ID, etc.),
save the extracted info as a dictionary and output it as a dataframe/csv file

Note: For uncertain cases a variable is set to 999 (eg. if it is not clear whether the plaintiff or defendant was granted physical custody, Stadigvarande boende = 999)

Outcome overview:
    1: joint
    2: sole with plaintiff (karande)
    3: sole with defendant (svarande)
    4: dismissed
    
Notes:
    Sometimes judge name is mistakenly read in after domskal heading, try to capture this maybe with strict restriction of 
    paragraph between? otherwise the code will always find 'something' after domskal

"""

import re, io, glob, shutil, pandas as pd

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

#Define Paths
pdf_dir = "P:/2020/14/Tingsrätter/ÖÖ_Case_Sorting_SC/Domar/all_cases/Check"
output_path = r'P:/2020/14/Kodning/custody_data.csv'

#Define key functions
def findSentence(string, part):
    sentenceRes = [sentence + '.' for sentence in part.split('.') if string in sentence]
    sentenceString = ''.join(sentenceRes)
    return sentenceString

def searchKey(string, part, g):
    finder = re.compile(string)
    match = finder.search(part)
    if match is not None:
        searchResult = match.group(g)
        return searchResult
    
def searchLoop(searchDict, part, g):
    for i in searchDict:
        result = searchKey(searchDict[i], part, g)
        if result is None:
            continue
        else: 
            break
    return result

def termLoop(termList, part):
    for term in termList:
        if term in part:
            dummy = 1
        else:
            dummy = 0
    return dummy

def city(string,i):
    stringList = list(string.split(" "))
    length = len(stringList)
    return stringList[length-i]

 

"""
sample_files = ["P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 1469-20 Dom 2020-07-03.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 5226-14 Dom 2015-11-16.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 3347-19 Dom 2019-09-13.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 3780-08 Dom 2009-04-08.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 3950-12 Dom 2013-05-15.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2925-14 Dom 2014-09-26.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 3376-09 Dom 2011-04-12.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 1198-19 Dom 2019-08-06.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 1558-16 Dom 2016-08-29.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 154-09 Dom 2010-10-13.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 5832-09 Dom 2011-11-28.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2526-14 Dom 2015-11-02.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2711-14 Dom 2015-04-16.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2351-12 Dom 2013-04-16.pdf",	"P:/2020/14/Tingsrätter/Västmanland/Domar/all_cases/Västmanlands TR T 2703-08 Dom 2009-07-06.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4419-19 Dom 2019-11-25.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 4527-12 Dom 2013-08-14.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2456-14 Dom 2015-12-23.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3447-11 Dom 2012-08-24.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 5117-19 Dom 2019-11-29.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 2023-14 Dom 2014-09-04.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3528-13 Dom 2013-11-15.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 3292-13 Dom 2014-03-17.pdf",	"P:/2020/14/Tingsrätter/Växjö/Domar/all_cases/Växjö TR T 1248-16 Dom 2016-10-11.pdf"]
for file in sample_files:
    shutil.copy(file,pdf_dir)
"""  

#Read in PDFs
pdf_files = glob.glob("%s/*.pdf" % pdf_dir)
print(pdf_files)

#Initialize variables
noOfFiles = 0
noUnreadable = 0
countries = 'okänd  sekretess afghanistan  albanien  algeriet  andorra  angola  antigua och barbuda  argentina  armenien  australien  azerbajdzjan  bahamas  bahrain  bangladesh  barbados  belgien  belize  benin  bhutan  bolivia  bosnien och hercegovina  botswana  brasilien  brunei  bulgarien  burkina faso  burundi  centralafrikanska republiken  chile  colombia  costa rica  cypern  danmark  djibouti  dominica  dominikanska republiken  ecuador  egypten  ekvatorialguinea  elfenbenskusten  el salvador  eritrea  estland  etiopien  fiji  filippinerna  finland  frankrike  förenade arabemiraten  gabon  gambia  georgien  ghana  grekland  grenada  guatemala  guinea  guinea-bissau  guyana  haiti  honduras  indien  indonesien  irak  iran  irland  island  israel  italien  jamaica  japan  jemen  jordanien  kambodja  kamerun  kanada  kap verde  kazakstan  kenya  kina  kirgizistan  kiribati  komorerna  kongo-brazzaville  kongo-kinshasa  kroatien  kuba  kuwait  laos  lesotho  lettland  libanon  liberia  libyen  liechtenstein  litauen  luxemburg  madagaskar  malawi  malaysia  maldiverna  mali  malta  marocko  marshallöarna  mauretanien  mauritius  mexiko  mikronesiska federationen  moçambique  moldavien  monaco  mon-tenegro  mongoliet  myanmar  namibia  nauru  nederländerna  nepal  nicaragua  niger  nigeria  nordkorea  nordmakedonien  norge  nya zeeland  oman  pakistan  palau  panama  papua nya guinea  paraguay  peru  polen  portugal  qatar  rumänien  rwanda  ryssland  saint kitts och nevis  saint lucia  saint vincent och grenadinerna  salo-monöarna  samoa  san marino  são tomé och príncipe  saudiarabien  schweiz  senegal  seychellerna  serbien  sierra leone  singapore  slovakien  slovenien  somalia  spanien  sri lanka  storbritannien  sudan  surinam  sverige  swaziland  sydafrika  sydkorea  sydsudan  syrien  tadzjikistan  tanzania  tchad  thailand  tjeckien  togo  tonga  trinidad och tobago  tunisien  turkiet  turkmenistan  tuvalu  tyskland  uganda  ukraina  ungern  uruguay  usa  uzbekistan  vanuatu  vatikanstaten  venezuela  vietnam  vitryssland  zambia  zimbabwe  österrike  östtimor  '
                
#Define search terms
svarandeSearch = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE '
defendantNationality = 'medborgare i (\w+ )+sekretess'
party ='((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))\s*[,]\s*(\d{6,10}.?\s*(\d{4})?[,]?\s)?' 
nameCaps = '[A-Z]{2,}'
idNo ='(\d{6,10}.?.?(\d{4})?[,]?\s)'
appendixStart = '(Bilaga [1-9]|Bilaga A|sida\s+1\s+av)'
searchCaseNo = 'mål\s*(nr)?\s*t\s*(\d*.?.?\d*)'
namePlaceHolder = '(?i)((\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))'

dateSearch = {
    '1' : 'dom\s+(\d*-\d*-\d*)',
    '2' : 'dom\s+sid\s*1\s*[(][0-9]*[)]\s*(\d*-\d*-\d*)',
    '3' : '(\d*-\d*-\d*)'
    }
courtSearch = {
    '1' : '((\w+ ){1})tingsr?.?ätt',
    '2' : '((\w+){1})[.]?.?tingsratt'
    }
judgeSearch = {
    '1' : '(?i)på (tings)?rättens vägnar\s*/i' + namePlaceHolder,
    '2' : '(?i)prövningstillstånd krävs.\s*(som ovan,|å rättens vägnar)?\s*' + namePlaceHolder,
    '3' : 'ÖVERKLAGANDE ([\w+ ]+\w+[.]\s?)+\s?' + namePlaceHolder,
    '4' : '(Hovrätten över Skåne och Blekinge|[(]?Svea hovrätt[)]?|Göta hovrätt|Hovrätten för Västra Sverige|Hovrätten för Nedre Norrland|Hovrätten för Övre Norrland)[.]?\s*(([A-Z]\w+\s?-?(\w+\s?-?)+?){1}((\w+\s?-?)*\w+))',
    '5' : '(?i)(\sför tingsrätten\s|för västra sverige)[.]?\s*' + namePlaceHolder
    }

#Define keys for simple word search
fastInfoKey = ['snabbupplysning', 'upplysning', 'upplysningar', 'yttrande']
corpTalksKey = ['samarbetssamtal','medlingssamtal','medling', 'medlare']
mainHearingKey = ['huvudförhandling' , 'rättegång' , 'sakframställning' , 'förhör' , 'nämnd']
lawyerKey = ["ombud", 'god man',  'advokat']
investigationKey = ['vårdnadsutredning','boendeutredning','umgängesutredning']
falseJudgeName = ['domskäl', 'yrkanden', 'avgörandet', 'överklag', 'tingsrätt']
cleanJudgeKey = ["(?i)(i avgörandet|i målets|i avgrandet|tingsrätt)\s*(\w+\s*)+","(?i)domskäl"]
cleanJudgeList = []

#Intiialize lists and dictionary to fill
data = {'Barn':[], 'Målnr':[], 'Tingsrätt':[], 'År avslutat':[], 'Deldom':[], 'Kärande förälder':[], 'Svarande förälder':[], 'Kär advokat':[], 'Sv advokat':[], 'Sv utlandet':[], 'Sv okontaktbar':[], 'Utfall':[], 'Umgänge':[], 'Stadigvarande boende':[], 'Underhåll':[], 'Enl överenskommelse':[], 'Snabbupplysning':[], 'Samarbetssamtal':[], 'Utredning':[], 'Huvudförhandling':[], 'Domare':[], "Page Count": [], 'Rättelse': [], "File Path": []}

#Loop over files and extract data
for file in pdf_files:
    pageCount = 0
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8-sig'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages_text = []
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
            read_position = retstr.tell()
            interpreter.process_page(page)
            retstr.seek(read_position, 0)
            page_text = retstr.read()
            page_text_clean = ' '.join((''.join(page_text)).split())
            pages_text.append(page_text_clean)
            pageCount += 1
             
    #Convert full text to clean string
    firstPage = pages_text[0]
    if "Rättelse" in firstPage:
        fullTextOG = ''.join(pages_text[1:])
        firstPage = ''.join(pages_text[1])
    else:
        fullTextOG = ''.join(pages_text)
        
    splitTextOG = re.split('_{10,40}', fullTextOG)
    
    if len(splitTextOG) > 1: 
        noOfFiles += 1                                                      
        rulingString = splitTextOG[1].lower() 
        headerOG = re.split('_{10,40}', firstPage)[0]   
        header = headerOG.lower()    
        appendixPage = [i for i, item in enumerate(pages_text) if re.search(appendixStart, item)]
        if not appendixPage:
            appendixPageNo = len(pages_text)
        else:
            appendixPageNo = appendixPage[0]
        lastPageOG = pages_text[appendixPageNo-1]
        lastPage = lastPageOG.lower()                       
        fullText = (re.split(appendixStart, fullTextOG)[0]).lower()   
        rulingOnly = re.split('(_{15,35}|-{15,35}|yrkanden)', rulingString)[0]   
        fullTextList = fullText.split(".")            
        
        print("Currently reading:")
        print(file)
        print(lastPageOG)
        
        try:
            svarandeStringOG = re.split(svarandeSearch, headerOG)[1] 
            kärandeStringOG = re.split('Kärande|KÄRANDE', (re.split(svarandeSearch, headerOG)[0]))[1]
            if svarandeStringOG == "":
                svarandeStringOG = re.split(svarandeSearch, headerOG)[2] 
            elif len(kärandeStringOG.split()) < 4:
                svarandeStringOG = re.split("SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerOG)[1]
                kärandeStringOG = re.split('KÄRANDE och SVARANDE|KÄRANDE OCH GENSVARANDE', (re.split("SVARANDE och KÄRANDE|SVARANDE OCH GENKÄRANDE ", headerOG)[0]))[1]
        except IndexError:
            try:
                svarandeStringOG = re.split('_{10,40}', (re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerOG)[1]))[1]))[1]))[0]
                kärandeStringOG = re.split('2[.]\s*', (re.split('1[.]\s*', (re.split('PARTER|Parter', headerOG)[1]))[1]))[0]
            except IndexError:
                svarandeStringOG = re.split("Hustrun|HUSTRUN", headerOG)[1] 
                kärandeStringOG = re.split('Mannen|MANNEN', (re.split("Hustrun|HUSTRUN", headerOG)[0]))[1]
        svarandeString = svarandeStringOG.lower()
        kärandeString = kärandeStringOG.lower()

        #List of children's numbers
        childNoRes = set(re.findall('\d{6,8}\s?-\d{4}', rulingString))
        
        #Loop to create dictionary with one row per child
        for i in childNoRes:                                               
            i = ''.join(i.split())                                          
            data['Barn'].append(i)
            
            #Get child's name
            try:
                childNameKey = ('(([A-Z]\w+ )+([A-Z]\w+)),\s*' + i )
                childNameFirst = searchKey(childNameKey, fullTextOG, 2).lower()
            except AttributeError:
                childName = 'not found'

            #Add file path and page count for each observation/pdf
            data["File Path"].append(file)
            data["Page Count"].append(pageCount)
            
            #Case ID for child i
            caseNo = ''.join((searchKey(searchCaseNo, header, 2)).split())
            data['Målnr'].append(caseNo)
            
            #Rättelse
            if 'rättelse' in header:
                dummy = 1
            else:
                dummy = 0
            data['Rättelse'].append(dummy)

            #District Court
            courtName = searchLoop(courtSearch, fullText, 0)
            data["Tingsrätt"].append(courtName)

            #Year Closed
            date = searchLoop(dateSearch, header, 1)
            data['År avslutat'].append(date)
            
            #Deldom
            if 'deldom' in file:
                dummy = 1
            else:
                dummy = 0
            data['Deldom'].append(dummy)
            
            #Plaintiff
            plaintNameFull = kärandeStringOG.split(",")[0]
            try:
                plaintNameFirst = searchKey(nameCaps, plaintNameFull, 0).lower()
            except AttributeError:
                plaintNameFirst = plaintNameFull.split()[0].lower()
            try:
                plaintNo = ''.join(searchKey(idNo, kärandeString, 0).split())
            except AttributeError:
                plaintNo = "-"
            data['Kärande förälder'].append(plaintNo) 

            # Defendant
            svNameFull = svarandeStringOG.split(",")[0]
            try:
                svNameFirst = searchKey(nameCaps, svNameFull, 0).lower()
            except AttributeError:
                svNameFirst = svNameFull.split()[0].lower()
            try:
                svNo = ''.join(searchKey(idNo, svarandeString, 0).split())
            except AttributeError:
                svNo = "-"
            data['Svarande förälder'].append(svNo)            
             
            #Plaintiff representative (Kär advokat)
            if 'ombud' in kärandeString or "god man" in kärandeString or "advokat" in kärandeString:
                dummy = 1
            else:
                dummy = 0 
            data['Kär advokat'].append(dummy)

            #Dummy defendant representative, defendant abroad
            for term in lawyerKey:
                if term in svarandeString:
                    defOmbud = 1 
                    defAddress = re.split(term, svarandeString)[0]
                    cityString = ''.join(city(defAddress, 2))
                    if cityString in countries:
                        abroadDummy = 1
                else:
                    defOmbud = 0
                    abroadDummy = 0
            data['Sv advokat'].append(defOmbud)
            data['Sv utlandet'].append(abroadDummy)
            
            #Defendant unreachable
            svUnreach1 = (re.compile(('(han|hon) har inte kunnat få kontakt med ' + svNameFirst))).search(fullText)
            svUnreach2 = (re.compile(('(han|hon) har inte lyckats etablera kontakt med ' + svNameFirst))).search(fullText)

            if 'okontaktbar' in fullText:
                if svNameFirst in findSentence('förordnat god man', fullText):
                    dummy = 1
                else:
                    dummy = 0
            elif svUnreach1 is not None or svUnreach2 is not None:
                dummy = 1
            elif 'förordnat god man' in fullText:
                if svNameFirst in findSentence('förordnat god man', fullText):
                    dummy = 1
                else:
                    dummy = 0
            elif 'varken kan bestrida eller medge' in fullText:
                dummy = 1
            elif 'inte fått någon kontakt' in fullText:
                if 'huvudman' in findSentence('någon kontakt', fullText) or svNameFirst in findSentence('någon kontakt', fullText):
                    dummy = 1
                else:
                    dummy = 999
            elif cityString == 'okänd': #CHECK ACCURACY OF THIS 
                dummy = 1
            else:
                dummy = 0
            data['Sv okontaktbar'].append(dummy)
            
            #Outcome
            i = findSentence('gemensam', rulingOnly)
            k = 'vårdn' in i
            if ('ska gemensamt ha vårdnaden om' in i) or ('vårdn' in rulingOnly and 'fortsätt' in i and 'ska' in i) or (k and 'alltjämt ska' in i) or (k and'ska alltjämt' in rulingOnly) or (k and 'skall tillkomma' in rulingOnly): 
                    dummy = 1
                    print("1")
            elif 'vårdn' in findSentence('ensam', rulingOnly): 
                if plaintNameFirst in findSentence('ensam', rulingOnly):
                    dummy = 2
                    print("2")
                elif svNameFirst in findSentence('ensam', rulingOnly):
                    dummy = 3
                    print("3")
            elif 'käromalet ogillas' in rulingOnly or "lämnas utan bifall" in rulingOnly:
                dummy = 4  
                print("4")
            elif 'ensam' in rulingOnly and 'vårdn' in rulingOnly: #IF THIS IS TOO NOISY TAKE IT OUT
                if plaintNameFirst in findSentence('vårdn', rulingOnly) or plaintNameFirst in findSentence('ensam', rulingOnly):
                    dummy = 2
                    print("5")
                if svNameFirst in findSentence('vårdn', rulingOnly) or svNameFirst in findSentence('ensam', rulingOnly):
                    dummy = 3
                    print("6")
            elif 'vårdn' in rulingOnly and 'överflytt' in rulingOnly:
                transferToDef = 'till ' + svNameFirst
                transferToPlaint = 'till ' + plaintNameFirst
                if transferToDef in findSentence('vårdn', rulingOnly):
                    dummy = 3
                    print("7")
                if transferToPlaint in findSentence('vårdn', rulingOnly):
                    dummy = 2
                    print("8")
            elif 'vårdn' in rulingOnly and 'tillerkänn' in findSentence('vårdn', rulingOnly): 
                if svNameFirst in findSentence('tillerkänn', rulingOnly):
                    dummy = 3
                    print("9")
                elif plaintNameFirst in findSentence('tillerkänn', rulingOnly):
                    dummy = 2
                    print("10")
            elif 'bilaga' in rulingOnly and 'överens' in findSentence('bilaga', rulingOnly):
                dummy = 999
                print("11")
            elif 'vårdn' not in rulingOnly or 'vårdn' in rulingOnly and 'påminns' in findSentence('vårdn', rulingOnly) or 'vårdn' in rulingOnly and 'påminn' in findSentence('vårdn', rulingOnly):
                #No custody ruling in this court record
                dummy = 17  
                print("12")
            else: 
                dummy = 999
                print("13")
            data['Utfall'].append(dummy)    
            
            #M.Visitation rights
            if 'umgänge' in rulingOnly:  
                if 'semester' in rulingOnly or 'avslår' in findSentence('umgänge', fullText):
                    dummy = 0
                elif 'bilaga' in rulingOnly:
                    if 'sidorna' in findSentence('bilaga', fullText):
                        dummy = 999
                #If umgänge is found in rulingOnly but NOT semester or avslar
                else:
                    dummy = 1
            #If umgänge is not found in rulingOnly
            else:
                dummy = 0 
            data['Umgänge'].append(dummy)
            
            #N. Physical custody   
            if plaintNameFirst in findSentence('stadigvarande boende', rulingOnly):
                dummy = 1
            elif svNameFirst in findSentence('stadigvarande boende', rulingOnly):
                dummy = 2
            elif 'bo tillsammans' in rulingOnly:             
                if childNameFirst and plaintNameFirst in findSentence('bo tillsammans', fullText):
                    dummy = 1
                elif childNameFirst and svNameFirst in findSentence('bo tillsammans', fullText):
                    dummy = 2
                else:
                    dummy = 999
            elif 'bilaga' in rulingOnly:
                if 'sidorna' in findSentence('bilaga', fullText):
                    dummy = 999
            else:
                dummy = 0
            data['Stadigvarande boende'].append(dummy)
            
            #Alimony
            if 'underhåll' in fullText:
                dummy = 1 
            #Alimony sum
            elif 'bilaga' in rulingOnly:
                if 'sidorna' in findSentence('bilaga', fullText):
                    dummy = 999
            else:
                dummy = 0 
            data['Underhåll'].append(dummy)
                 
            #Ruling by agreement
            i = findSentence('överenskommelse', fullText)
            k = findSentence('överens', fullText)
            if 'överenskommelse' in fullText:
                if 'dom' and 'parterna' in i or 'framgår' and 'dom' in i or 'enlighet' and 'dom' in i or 'enligt' and 'dom' in i or 'följer' and 'dom' in i or 'fastställa' and 'dom' in i:
                    dummy = 1
                else:
                    dummy = 0
            elif "överens" in fullText:
                if 'parterna' in k and 'kommit' in k and 'barnets' in k and 'bästa' in k:
                    dummy = 1
                else:
                    dummy = 0
            else:
                dummy = 0 
            data['Enl överenskommelse'].append(dummy)
            
            #Fast information (snabbupplysningar)
            dummyInfo = termLoop(fastInfoKey, fullText)
            data['Snabbupplysning'].append(dummyInfo)
            
            #Cooperation talks
            dummyCorp = termLoop(corpTalksKey, fullText)
            data['Samarbetssamtal'].append(dummyCorp)
            
            #Investigation
            dummyInve = termLoop(investigationKey, fullText)
            data['Utredning'].append(dummyInve)
                        
            #Main hearing 
            for term in mainHearingKey:
                if term in fullText:
                    if 'utan' in findSentence(term, fullText) or 'inför' in findSentence(term, fullText):
                        dummy = 0
                        break
                    else:
                        dummy = 1
                        break
                else:
                    dummy = 0
            data['Huvudförhandling'].append(dummy)

            #Name of judge
            judgeName = searchLoop(judgeSearch, lastPageOG, 2)
            if judgeName is None:
                judgeName = findSentence('nämndemännen', lastPageOG) #check if these two lines of code return the same thing
                if judgeName == '':
                    judgeName = fullTextList[-1] #check if these two lines of code return the same thing, if so, keep only this
            for term in falseJudgeName:
                if term in judgeName:
                    judgeName = fullTextList[-1]
                    for term in falseJudgeName:
                        if term in judgeName:
                            judgeName = ' '.join(fullTextList[-1].split()[-2:])
            #Clean judge name
            for term in cleanJudgeKey:
                cleanJudge = searchKey(term, judgeName, 0)
                if cleanJudge is not None:
                    cleanJudgeList.append(cleanJudge)
            for term in cleanJudgeList:
                judgeName = re.sub(term, '', judgeName).strip('_ ')
            data['Domare'].append(judgeName)
    else:
        print('Error: PDF at path %s not readable!' %(file))
        noUnreadable += 1
    
#Dataframe created from dictionary
df = pd.DataFrame(data)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)

#Save to csv
#df.to_csv(output_path, sep = ',', encoding='utf-8-sig')

print("---Saved as CSV---")



