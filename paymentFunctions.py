import pandas as pd
import numpy_financial as npf

def amortize_fixed(interest_rate, years, pv, fv, name=1):

    payments = 12
    payment_number = range(1, (payments * years) + 1) 

    schedule = pd.DataFrame(index=payment_number, 
                            columns = ["payment_num",
                                       "rate",
                                       "payment",
                                       "principle",
                                       "interest",
                                       "balance"])    
    schedule["payment_num"] = payment_number
    schedule["rate"] = interest_rate
    schedule["payment"] = abs(npf.pmt((schedule["rate"]/100)/payments, years * payments, pv, fv))
    schedule["principle"] = abs(npf.ppmt((schedule["rate"]/100)/payments, schedule.index, years * payments, pv))
    schedule["interest"] = abs(npf.ipmt((schedule["rate"]/100)/payments, schedule.index, years * payments, pv))

    schedule['cumlative_payment'] = schedule['payment'].cumsum()
    schedule['cumlative_interest'] = schedule['interest'].cumsum()
    schedule['cumlative_principle'] = schedule['principle'].cumsum()
    schedule['balance'] = pv - schedule['cumlative_principle']

    schedule = round(schedule, 2)
    schedule["type"] = "fixed"
    schedule["simulation"] = name

    return schedule

def amortize_variable(rates_df, rates_col, spread, years, pv, fv, name=1):
    payments = 12
    payment_number = range(1, (payments * years) + 1) 

    # initial set-up of the dataframe
    schedule_var = pd.DataFrame(index=payment_number)   
    schedule_var["payment_num"] = payment_number
    schedule_var["euribor"] = rates_df[rates_col]
    schedule_var["spread"] = spread
    schedule_var["rate"] = schedule_var["euribor"] + schedule_var["spread"]
    schedule_var["payments remaining"] = pd.DataFrame(range(0, (payments * years) + 2)[::-1])

    # populating the first row of data
    schedule_var['starting balance'] = schedule_var['payments remaining'].apply(
        lambda x: pv 
        if x == years * payments 
        else None)
   
    # calculating the first row of data
    schedule_var["payment"] = abs(npf.pmt((schedule_var["rate"]/100)/payments, schedule_var["payments remaining"], schedule_var["starting balance"], fv))
    schedule_var["interest"] = schedule_var["starting balance"] * ((schedule_var["rate"]/100)/payments)
    schedule_var["principle"] = schedule_var["payment"] - schedule_var["interest"]
    schedule_var["end balance"] =  schedule_var["starting balance"] - schedule_var["principle"]
    schedule_var = schedule_var.round(2)
    
    # loop to calculate all other rows
    for index in range(1, len(schedule_var) + 1):
        if index == 1:
            schedule_var.at[index, 'starting balance'] = pv
        else:        
            schedule_var.at[index, 'starting balance'] = schedule_var.at[index - 1, 'end balance']
            schedule_var.at[index, 'payment'] = abs(npf.pmt(((schedule_var.at[index, 'rate'] / 100) / payments), 
                                                            schedule_var.at[index, 'payments remaining'], 
                                                            schedule_var.at[index, 'starting balance']))
            schedule_var.at[index, 'interest'] =  schedule_var.at[index, 'starting balance'] * ((schedule_var.at[index, 'rate'] / 100) / payments)
            schedule_var.at[index, 'principle'] =  schedule_var.at[index, 'payment'] - schedule_var.at[index, 'interest']
            schedule_var.at[index, 'end balance'] = schedule_var.at[index, 'starting balance'] - schedule_var.at[index, 'principle']
    
    schedule_var['cumlative_payment'] = schedule_var['payment'].cumsum()
    schedule_var['cumlative_principle'] = schedule_var['principle'].cumsum()
    schedule_var['cumlative_interest'] = schedule_var['interest'].cumsum()
    schedule_var['balance'] = pv - schedule_var['cumlative_principle']

    schedule_var = round(schedule_var, 2)
    schedule_var["type"] = "variable" + " spread: " + str(spread) +"%"
    schedule_var["simulation"] = name
    
    return schedule_var
