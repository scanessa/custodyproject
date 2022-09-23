import re

header = '\nKärande och Svarande\nHeidi Edensvård, 780212-0043\nMedborgare i Finland\nParkgatan 754874 Gårdsjö\nOmbud: Advokaten Jan-Otto Meijer\nKronhusgatan 1141105 Göteborg\nSvarande och Kärande\nJonas Edensvård, 740919-5034\nMarklandsgatan 7141105 Göteborg\nOmbud: Advokaten Urban Gilborne\nVästra Hamngatan 1141117 Göteborg\nDDO'

party_split = r'\s(?=\w+ärande och Svarande|ÄRANDE OCH SVARANDE|Ombud|ombud|God man|\\\
    tällföreträdare|ökande|Hustrun|HUSTRUN|Mannen|MANNEN|Svarande)'
parties = re.split(party_split, header)


print(parties)