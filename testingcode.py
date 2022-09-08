import re
from searchterms import party_split
#header = '-\n1999-1202 Mål ar T 327-99\nmeddelad i\nLUND\nSÖKANDE\nMannen\nLennart Runesson, 560701-2738\nS:t Drottensgatan 462156 VISBY\nHustrun\nAnnica Runesson, 550624-2485\nOsten Undéns Gata 12222762 LUND\nOmbud och biträde enligt rättshjälpslagen:\nadvokaten Anna Rydén\nBox 120722105 LUND\nDDO'
header = '-\n1999-1202 Mål ar T 327-99\nmeddelad i\nLUND\n\nMannen\nLennart Runesson, 560701-2738\nS:t Drottensgatan 462156 VISBY\nHustrun\nAnnica Runesson, 550624-2485\nOsten Undéns Gata 12222762 LUND\nOmbud och biträde enligt rättshjälpslagen:\nadvokaten Anna Rydén\nBox 120722105 LUND\nDDO'
parties = re.split(party_split, header)

print(parties)