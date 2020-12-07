import csv
import dateutil.relativedelta as rd
import dateutil.parser as parser

# user inputs - file paths for budget and investments
while(True):
    pathToBudget = input("budget.csv:\t")
    pathToInv = input("investments.csv:\t")
    try:
        with open(pathToBudget, 'r') as budgetFile:
            budget = list(csv.DictReader(budgetFile))
        with open(pathToInv, "r") as invFile:
            inv = list(csv.DictReader(invFile))
    except FileNotFoundError:
        print("Budget/Investments file(s) not found. Enter paths of budget.csv and investments.csv again:")
    else:
        break

# Ensure Amounts and ID's are integers
for rule in budget:
    rule['Amount'] = int(float(rule['Amount']))
    rule['ID'] = int(float(rule['ID']))

for txn in inv:
    txn['Amount'] = int(float(txn['Amount']))
    txn['ID'] = int(float(txn['ID']))


'''
For every txn checked, maintain a running total of investments by month, quarter and year.
Reset the running total to 0 every time a given time delta passes:
    - month when month changes
    - quarter when quarter changes
    - year + quarter + month when year changes 
'''

# Set of different sectors across budget and investments
timePeriods = ["Year", "Month", "Quarter"]
sectors = set([txn["Sector"] for txn in inv if txn["Sector"] != ""]).union(set([rule["Sector"] for rule in budget if rule["Sector"] != ""]))

# Running totals
rTotals = dict()
rTotals['Month'] = {sector: 0 for sector in sectors}
rTotals['Quarter'] = {sector: 0 for sector in sectors}
rTotals['Year'] = {sector: 0 for sector in sectors}

# Utility functions
# 1. Parse dates of txns to get month and year
def parseDate(txn):
    month = parser.parse(txn["Date"], dayfirst = True).month
    year = parser.parse(txn["Date"], dayfirst = True).year
    return (month, year)

# 2. Set current Quarter end based on current month
def setCurrentQuarterEnd(currentMonthArg):
    currentMonthArg = int(currentMonthArg)
    if (currentMonthArg <= 3):
        return 3
    elif (currentMonthArg <= 6):
        return 6
    elif (currentMonthArg <= 9):
        return 9
    elif (currentMonthArg <= 12):
        return 12

# These values will be updated every time the month/year changes
(currentMonth, currentYear) = parseDate(inv[0])
# currentYear = parseDate(inv[0])
currentQuarterEnd = setCurrentQuarterEnd(currentMonth)

# 3. Set current month/qtr/year being processed 
#    and reset counters as time passes
def setCountersAndDates(txn):
    global currentMonth
    global currentYear
    global currentQuarterEnd
    global rTotals

    (txnMonth, txnYear) = parseDate(txn)
    if (txnYear == currentYear):
        pass
    else:
        # everything resets in the new year
        currentYear = txnYear
        currentMonth = txnMonth
        currentQuarterEnd = setCurrentQuarterEnd(currentMonth)
        rTotals = dict.fromkeys(timePeriods, {sector: 0 for sector in sectors})

    # if txn happened in the same month as last, do nothing
    if (txnMonth == currentMonth):
        pass
    else:
        currentMonth = txnMonth
        
        # reset running totals for month and (if reqd) quarter
        for sector in rTotals['Month']:
            rTotals['Month'][sector] = 0
        if ((currentMonth) > currentQuarterEnd):
            currentQuarterEnd = setCurrentQuarterEnd(currentMonth)
            for sector in rTotals['Quarter']:
                rTotals['Quarter'][sector] = 0


invalidTxns = list()

# # Checking txns - we set current month/year to that of first txn;
for txn in inv:
    flag = 0
    setCountersAndDates(txn)
    for rule in budget:
        # Case 1: time period + sector
        if (rule["Time Period"] != "" and rule["Sector"] != ""):
            if (txn['Sector'] != rule['Sector']):
                continue  
            elif (txn['Sector'] == rule['Sector']):
                if (txn['Amount'] + rTotals[rule['Time Period']][txn['Sector']] > rule['Amount']):
                    # Txn violates rule for given time period
                    # invalidTxns.append(txn)
                    flag = 1
                    break
               
        # Case 2: time period only
        if (rule['Time Period'] != "" and rule['Sector'] == ""):
            totalForTP = sum([rTotals[rule['Time Period']][sector] for sector in rTotals[rule['Time Period']]])
            if (totalForTP + txn['Amount'] > rule['Amount']):
                flag = 1
                break
            
        # case 3: Sector only - this is a limit on the amount for a single txn
        if (rule['Time Period'] == "" and rule['Sector'] != ""):
            if (txn['Sector'] != rule['Sector']):
                continue
            elif (txn['Sector'] == rule['Sector']):
                if (txn['Amount'] > rule['Amount']):
                    flag = 1
                    break
             
    if (flag == 1):
        invalidTxns.append(txn["ID"])
    else:
        for tp in timePeriods:
            rTotals[tp][txn["Sector"]] +=  txn["Amount"]

# All txns checked
# print("Checked all txns, invalid txns are:\n", invalidTxns, sep="\n")
for ID in invalidTxns:
    print(ID)