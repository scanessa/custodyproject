--- DESCRIPTION OF CUSTODY RESEARCH CODE FILES ---

-- domar_preprocessing
  Reads in all pdf files in given folder, extracts information per child ID found and saves this information as one line to custody_data.csv
  Information extracted: 
    Barn: child ID number, unique ID for observations
    Målnr
    Tingsrätt
    År avslutat
    Deldom: dummy = 1 if case is a deldom 
    Kärande förälder: plaintiff's ID number 
    Svarande förälder: defendant's ID number, = "-" if defendant has no ID number in court record 
    Kär advokat: dummy = 1 if plaintiff has a lawyer 
    Sv advokat: dummy = 1 if defendant has a lawyer 
    Sv utlandet: dummy = 1 if defendant is abroad 
    Sv okontaktbar: dummy = 1 if defendant is unreachable 
    Utfall: 1 = joint custody, 2 = sole with plaintiff (karande), 3 = sole with defendant (svarande), 4 = dismissed
    Umgänge: dummy = 1 if visitation rights were set in the ruling
    Stadigvarande boende: 1 = physical custody assigned to plaintiff, 2 = physical custody assigned to defendant, 0 = physical custody not assigned
    Underhåll: dummy = 1 if alimony is assigned in ruling
    Enl överenskommelse: dummy = 1 if ruling is by parental agreement  
    Snabbupplysning: dummy = 1 if code finds keyword that indicates fast information was given during trial
    Samarbetssamtal: dummy = 1 if code finds keyword that indicates cooperation talks between parties
    Utredning: dummy = 1 if code finds keyword that indicates an investigation into some aspect of the custody case (eg by a case worker)
    Huvudförhandling: dummy = 1 if code finds keyword that indicates a main hearing
    Domare: judge's name
    Page Count
    Rättelse: dummy = 1 if court record includes a correction
    File Path
    
-- court_docs_register
  Reads in all files in tingsrätter, loops through each file and extract information on X for all files and additionally on Y for files that are custody cases
  X:  case_id
      type
      court
      year
      plaintiff
      defendant
      judge
      filepath
  Y:  case_type
  
-- court_docs_register
  Reads in all files in a particular folder and moves the files to folders according to four categories: 
    1217 A - Äktenskapsskillnad\domar; divorce/custody battles (ideal case)
    1217 B - Äktenskapsskillnad\domar utan värdnadstvist; divorce with no custody battles
    1216 A - Vårdnad\domar; custody battles of non-divorcing parents
    1216 B - Vårdnad\domar där socialfärvaltning är kärande eller svarande; legal guardian cases

-- workorders_lottery
  Reads in work orders in given folder, searchers for the word lottery and saves information on date, court, and a dummy of whether lottery was found in the 
  doc to a csv
  
  
