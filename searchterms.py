# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 12:04:28 2022

@author: ifau-SteCa

File to provide dictionaries, strings and lists with searchterms for building
the court rulings and custody cases databases
"""

#Cleaning OCR
OCR_CORR = {
    'Kiärande':'Kärande',
    'KIÄRANDE':'KÄRANDE',
    'Mal':'Mål',
    'Mäl':'Mål',
    'Domskill':'Domskäl',
    'DOMSKILL':'DOMSKÄL',
    '\x0c':''
    }

#Define search terms
allLetters = '[A-ZÅÐÄÖÉÜÆØÞ][a-zåäáïüóöéæøßþîčćžđšžůúýëçâêè]'
appendix_start = '((?<!se )Bilaga 1|(?<!se )Bilaga A|sida\s+1\s+av)'
capLetters = '[A-ZÅÐÄÖÉÜÆØÞ]'
citizen = 'medbor[a-z]*\s*i\s*[a-z]*'

defend_search = ' Svarande|SVARANDE|Motpart|MOTPART|SVARANDE och KÄRANDE |MANNEN|Mannen'
id_pattern ='((\d{6,10}.?.?(\d{4})?)[,]?\s)'

caseno_search = {
    '1':'må.\s*(nr)?[.]?\s*t\s*(\d*\s*.?.?\s*\d*)',
    '2':'\s(t)\s*(\d{2,5}.\d{2})',
    '3':'\n(t)\s*(\d{2,5}.\d{2})',
    }
    
date_search = {
    '1' : 'dom\s+(\d{4}-\d{2}-\d{2})',
    '2' : 'dom\s+(\d*-\d*-\d*)',
    '3' : 'dom\s+sid\s*1\s*[(][0-9]*[)]\s*(\d*-\d*-\d*)',
    '4' : '(\d{4}-\d{2}-\d{2})'
    }

judgesearch = {
    '1': '\n\s*\n\s*((' + allLetters + '+\s+){2,4})\n\s*\n', #normal names
    '2': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)\n\s*\n', #first name hyphenated
    '3': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)\n\s*\n', #last name hypthenated
    '4': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n\s*\n', #first and last name hyphenated
    '5': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #name with initial as second name
    '6': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)\n\s*\n', #first and second name as initial
    #if there is a note in the line following the judge's name
    '7': '\n\s*\n\s*((' + allLetters + '+\s*){2,4})\n', #normal names
    '8': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*)\n', #first name hyphenated
    '9': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s*)\n', #last name hypthenated
    '10': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s*)\n', #first and last name hyphenated
    '11': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + 's\s' + allLetters + '+\s*)\n', #name with initial as second name
    '12': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s*)\n', #name with initial as second name
    #For documents where judge didnt sign
    '13': 'rådmannen\s*((' + allLetters + '+\s+){2,4})',
    '14': 'rådmannen\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*)', #first name hyphenated
    '15': 'rådmannen\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s*)', #last name hypthenated
    '16': 'rådmannen\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s*)', #first and last name hyphenated
    '17': 'rådmannen\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s*)', #name with initial as second name
    '19': 'rådmannen\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s*)', #name with initial as second name
    '20': 'tingsfiskalen\s*((' + allLetters + '+\s+){2,4})',
    '21': 'tingsfiskalen\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*)', #first name hyphenated
    '22': 'tingsfiskalen\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s*)', #last name hypthenated
    '23': 'tingsfiskalen\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)', #first and last name hyphenated
    '24': 'tingsfiskalen\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s*)', #name with initial as second name
    '24a': 'tingsfiskalen\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s*)', #name with initial as second name
    #when judge's name ends with .
    '25': '\n\s*\n\s*((' + allLetters + '+\s+){1,3}' + allLetters + '+).\s*\n\n', #normal names
    '26': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+).\s*\n', #first name hyphenated
    '27': '\n\s*\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+).\s*\n', #last name hypthenated
    '28': '\n\s*\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + ').\s*\n', #first and last name hyphenated
    '29': '\n\s*\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+).\s*\n', #name with initial as second name
    '30': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s*).\s*\n', #name with initial as second name
    #Only one new line before judge's name
    '31': '\n\s*((' + allLetters + '+\s+){2,4})\n\s*\n', #normal names
    '32': '\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+)\s*\n\s*\n', #first name hyphenated
    '33': '\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+)\s*\n\s*\n', #last name hypthenated
    '34': '\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n\s*\n', #first and last name hyphenated
    '35': '\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+)\s*\n\s*\n', #name with initial as second name
    '36': '\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+)\s*\n\s*\n', #name with initial as second name
    #Only one new line before judge's name and one new line after (for scans)
    '37': '\n\s*((' + allLetters + '+\s*){2,4})\n', #normal names
    '38': '\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+)\s*\n', #first name hyphenated
    '39': '\n\s*(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+)\s*\n', #last name hypthenated
    '40': '\n\s*(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)\n', #first and last name hyphenated
    '41': '\n\s*(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+)\s*\n', #name with initial as second name
    '42': '\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+)\s*\n' #name with initial as second name
    
    }

judgesearch_scans = {
    '1': '((' + allLetters + '+\s+){2,4})', #normal names
    '2': '(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s+)', #first name hyphenated
    '3': '(' + allLetters + '+\s' + allLetters + '+-' + allLetters + '+\s+)', #last name hypthenated
    '4': '(' + allLetters + '+\s*-\s*' + allLetters + '+\s' + allLetters + '+\s*-\s*' + allLetters + '+\s+)', #first and last name hyphenated
    '5': '(' + allLetters + '+\s' + capLetters + '\s' + allLetters + '+\s+)', #name with initial as second name
    '6': '\n\s*\n\s*(' + capLetters + '\s' + capLetters + '\s' + allLetters + '+\s+)', #first and second name as initial
    
    }

judgesearch_noisy = {
    '1': '\n\s*\n(.*)'
    }

judgeProtokollPreffix = '(Lagmannen|lagmannen|Rådmannen|rådmannen|notarien|Beredningsjuristen|beredningsjuristen|tingsfiskalen|Tingsfiskalen)'
suff1 = '[,|;]?\s*[(]?'
suff2 = '((\w+)?\s*(Protokollförare|protokollförare|ordförande))?'
suff3 = '[)]?\s*([A-ZÅÄÖ]{2,})'
judgeProtokollSuffix = suff1 + suff2+ suff3

judgetitle_search = {
    '1': judgeProtokollPreffix + '\s*(([A-ZÅÄÖ][a-zåäöé]+\s*){2,4})' + judgeProtokollSuffix, #normal names
    '2': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #first name hyphenated
    '3': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #last name hypthenated
    '4': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ][a-zåäöé]+-[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #first and last name hyphenated
    '5': judgeProtokollPreffix + '\s*([A-ZÅÄÖ][a-zåäöé]+\s[A-ZÅÄÖ]\s[A-ZÅÄÖ][a-zåäöé]+\s+)'+ judgeProtokollSuffix, #name with initial as second name
    '6': judgeProtokollPreffix + '\s*(([A-ZÅÄÖ][a-zåäöé]+\s*){1})' + '[,|;]?\s*[(]?((\w+) [p|P]rotokollförare)?[)]?\s*([A-Z])' #only last name 
    }

ruling_search = {
    '1':'\n\s*\n\s*[A-ZÅÄÖ., ]{3,}\s*\n',
    '2':'YRKANDEN',
    '3':'\nYrkanden'
    }

#Define keys for simple word search
agreement_key = ['samförståndslösning',  'överens ', 'medger', 'medgett', ' ense ', 'överenskommelse',
                    'medgivande', 'överenskommit', 'över- ens ', 'medgivit', 'enats ']
agreement_add = ['framgår' ,'följer','fastställa', 'bäst', 'vård', 'fastställa', 'yrkande']
agreement_excl = ['med sin', 'bestr', ' talan ', 'avgjord', 'inte ', 'alla frågor som rör barnen'] 

countries = ['saknas', 'u.s.a.', 'u.s.a', 'usa', 'afghanistan', 'albanien', 'algeriet', 'andorra', 'angola', 'antigua och barbuda', 'argentina', 'armenien', 'australien', 'azerbajdzjan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belgien', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnien och hercegovina', 'botswana', 'brasilien', 'brunei', 'bulgarien', 'burkina faso', 'burundi', 'centralafrikanska republiken', 'chile', 'colombia', 'costa rica', 'cypern', 'danmark', 'djibouti', 'dominica', 'dominikanska republiken', 'ecuador', 'egypten', 'ekvatorialguinea', 'elfenbenskusten', 'el salvador', 'eritrea', 'estland', 'etiopien', 'fiji', 'filippinerna', 'finland', 'frankrike', 'förenade arabemiraten', 'gabon', 'gambia', 'georgien', 'ghana', 'grekland', 'grenada', 'guatemala', 'guinea', 'guinea-bissau', 'guyana', 'haiti', 'honduras', 'indien', 'indonesien', 'irak', 'iran', 'irland', 'island', 'israel', 'italien', 'jamaica', 'japan', 'jemen', 'jordanien', 'kambodja', 'kamerun', 'kanada', 'kap verde', 'kazakstan', 'kenya', 'kina', 'kirgizistan', 'kiribati', 'komorerna', 'kongo-brazzaville', 'kongo-kinshasa', 'kroatien', 'kuba', 'kuwait', 'laos', 'lesotho', 'lettland', 'libanon', 'liberia', 'libyen', 'liechtenstein', 'litauen', 'luxemburg', 'madagaskar', 'malawi', 'malaysia', 'maldiverna', 'mali', 'malta', 'marocko', 'marshallöarna', 'mauretanien', 'mauritius', 'mexiko', 'mikronesiska federationen', 'moçambique', 'moldavien', 'monaco', 'montenegro', 'mongoliet', 'myanmar', 'namibia', 'nauru', 'nederländerna', 'nepal', 'nicaragua', 'niger', 'nigeria', 'nordkorea', 'nordmakedonien', 'norge', 'nya zeeland', 'oman', 'pakistan', 'palau', 'panama', 'papua nya guinea', 'paraguay', 'peru', 'polen', 'portugal', 'qatar', 'rumänien', 'rwanda', 'ryssland', 'saint kitts och nevis', 'saint lucia', 'saint vincent och grenadinerna', 'salo-monöarna', 'samoa', 'san marino', 'são tomé och príncipe', 'saudiarabien', 'schweiz', 'senegal', 'seychellerna', 'serbien', 'sierra leone', 'singapore', 'slovakien', 'slovenien', 'somalia', 'spanien', 'sri lanka', 'storbritannien', 'sudan', 'surinam', 'swaziland', 'sydafrika', 'sydkorea', 'sydsudan', 'syrien', 'tadzjikistan', 'tanzania', 'tchad', 'thailand', 'tjeckien', 'togo', 'tonga', 'trinidad och tobago', 'tunisien', 'turkiet', 'turkmenistan', 'tuvalu', 'tyskland', 'uganda', 'ukraina', 'ungern', 'uruguay', 'usa', 'uzbekistan', 'vanuatu', 'vatikanstaten', 'venezuela', 'vietnam', 'vitryssland', 'zambia', 'zimbabwe', 'österrike', 'östtimor']
cities = ['alingsås', 'arboga', 'arvika', 'askersund', 'avesta', 'boden', 'bollnäs', 'borgholm', 'borlänge', 'borås', 'djursholm', 'eksjö', 'enköping', 'eskilstuna', 'eslöv', 'fagersta', 'falkenberg', 'falköping', 'falsterbo', 'falun', 'filipstad', 'flen', 'gothenburg', 'gränna', 'gävle', 'hagfors', 'halmstad', 'haparanda', 'hedemora', 'helsingborg', 'hjo', 'hudiksvall', 'huskvarna', 'härnösand', 'hässleholm', 'höganäs', 'jönköping', 'kalmar', 'karlshamn', 'karlskoga', 'karlskrona', 'karlstad', 'katrineholm', 'kiruna', 'kramfors', 'kristianstad', 'kristinehamn', 'kumla', 'kungsbacka', 'kungälv', 'köping', 'laholm', 'landskrona', 'lidingö', 'lidköping', 'lindesberg', 'linköping', 'ljungby', 'ludvika', 'luleå', 'lund', 'lycksele', 'lysekil', 'malmö', 'mariefred', 'mariestad', 'marstrand', 'mjölby', 'motala', 'nacka', 'nora', 'norrköping', 'norrtälje', 'nybro', 'nyköping', 'nynäshamn', 'nässjö', 'oskarshamn', 'oxelösund', 'piteå', 'ronneby', 'sala', 'sandviken', 'sigtuna', 'simrishamn', 'skanör', 'skanör med falsterbo', 'skara', 'skellefteå', 'skänninge', 'skövde', 'sollefteå', 'solna', 'stockholm', 'strängnäs', 'strömstad', 'sundbyberg', 'sundsvall', 'säffle', 'säter', 'sävsjö', 'söderhamn', 'söderköping', 'södertälje', 'sölvesborg', 'tidaholm', 'torshälla', 'tranås', 'trelleborg', 'trollhättan', 'trosa', 'uddevalla', 'ulricehamn', 'umeå', 'uppsala', 'vadstena', 'varberg', 'vaxholm', 'vetlanda', 'vimmerby', 'visby', 'vänersborg', 'värnamo', 'västervik', 'västerås', 'växjö', 'ystad', 'åmål', 'ängelholm', 'örebro', 'öregrund', 'örnsköldsvik', 'östersund', 'östhammar']
cooperation_key = ['samarbetssamtal','medlingssamtal',' medling', ' medlare']
contest_key = [['bestritt'], ['bestridit'], ['har','för','egen','del','yrkat'], ['har','istället','yrkat'],['som','slutligen','bestämt','i','sin','talan']]

exclude_phys = ['jämna' , 'växelvis', 'skyddat']
exclude_judge = ['telefon','telefax', 'svarande', 'DOM', 'dom', '1']

fastinfo_key = ['snabbupplysning', 'upplysning', 'snabbyttrande']
footer = ['telefax', 'e-post', 'telefon', 'besöksadress', 'postadress', 'expeditionstid', 'dom']

invest_key = ['vårdnadsutredning','boendeutredning','umgängesutredning']

lawyer_key = ["ombud:", 'god man:',  'advokat:', "ombud", 'god man',  'advokat']
legalguardian_terms = ["social", "kommun", "nämnden", "stadsjurist", 'stadsdel', 'familjerätt']

mainhearing_key = ['huvudförhandling' , ' rättegång ' , 'sakframställning' , ' förhör ', 
                   'tingsrättens förhandling','huvud- förhandling' ]

nocontant = ['någon', 'inte']
no_vard = ['umgänge', 'boende', ' bo ']

outcomes_key = ["vård", "umgänge", "boende"]

# Include annan bedömning to take care of double negative (eg INTE annan bedömning should not count as rejection)
past = ['inledningsvis', 'annan bedömning']

# don't use ' ska ' to capture skall as well
physicalcust_list = [['boende'],['bo tillsammans'],[' ska',' bo '],[' ska','bosatt']] 
physicalcust = ['boende','bo tillsammans',' bo ',' ska ','bosatt']

residence_key = [['kvarsittningsrätt'], ['har','rätt','att',' kvar','bo ','gemensamma','bostad','till','bodelning','sker']]
reject = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga '] 
reject_invest = ['avskriv',' ogilla','utan bifall','avslå',' inte ',' inga ', ' utöva '] 
reject_outcome = ['avskriv',' ogilla','utan bifall','avslå',' inte ','skrivs', 'kvarstå', ' inga ', 'utan']  
reject_mainhearing = ['skulle ', 'utan', ' ingen', 'inför huvudförhandling']


remind_key = ['bibehålla' ,'påminn' ,'erinra' ,'upply', 'kvarstå', 'fortfarande ']

separation_key = ['separera', 'relationen tog slut', 'förhållandet tog slut', 'relationen avslutades', 
                 'förhållandet avslutades', 'skildes', 'skiljas', 'skiljer' ]

unwanted_judgeterms = ['blekinge','bilaga','den','för','ges','ha','hovrätt','hovrätten',
                       'inkommit','in','inlagan','januari','juni','men','mening','november',
                       'över','och','överklagande','prövningstillstånd','på','protokollsbilaga',
                       'skall','senast','ställt','skåne','ställs','skiljaktig','se',
                       'sverige','svea','tingsrätten','tingsrättens','till',
                       'vägnar','vagnar','västra'
                      ]

visitation_key = ['umgänge', 'umgås']

















