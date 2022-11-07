from fuzzywuzzy import fuzz

part = '\n ela hovde, ragnhild eva marie, 621226-4904\nlillebyvägen 4642383 torslanda'
n = "stella"

print(fuzz.token_set_ratio(n, part))