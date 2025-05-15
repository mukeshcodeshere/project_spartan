# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 15:46:19 2022

@author: raulrivera
"""

import time
from GvWSConnection import *
from PriceUtilites import * 
import numpy as np
import sys
from datetime import timedelta, datetime as dt

USERNAME = 'GCC018'
PASSWORD = 'password'


conn = GvWSConnection(USERNAME, PASSWORD)

def getSeasonalPrices(contractIn,contractOut,monthIn,yearsListIn) :
    
    startDate = '1/1/2000'
    
    contractList = []
    contractOut = []
    for x in yearsListIn :
        
        if '#' in contractIn :
            
            contractList.append( contractIn  + monthIn + str(x))
        else:
            contractList.append( '/'+ contractIn  + monthIn + str(x))
                          
        contractOut.append( contractIn  + '_' + monthIn + str(x))  
    try :    
        d1 = conn.get_daily(contractList, start_date = dt.strptime(startDate ,'%m/%d/%Y'))
        
    except :
        d1 = conn.get_daily(contractList, start_date = dt.strptime(startDate ,'%m/%d/%Y'))
    # nameOut = ['14','15','16','17','18','19','20','21','22']

    xx = createDailyDataMV(d1,contractList,contractOut)
    
    return xx


def contractMonths(expireIn,contractIn) :
    
    contractMonths = expireIn[expireIn.index > dt.today()].copy()
    
    expireDate =  contractMonths[contractMonths['MonthCode']== contractIn]
    
    return expireDate.iloc[0,:]


def yearList(lastTradeIn,yearsBackIn,typeIn,contractIn1,contractIn2,futuresContractDictIn) :
    
    curYearInt = lastTradeIn['Year'] % 100 #Keep only last two digets of yeat
    
    # if contractIn1 == 'F' :
        
    #     curYearInt = int(lastTradeIn[-2:]) +1 #Accounts for Jan being year +1 
        
    # else :
        
    #     curYearInt = int(lastTradeIn[-2:])
    
    yearList1 =[]
    yearList2 = []
    
        
    for i in range(curYearInt - yearsBackIn,curYearInt+1) :
        
        y1Temp = i
        
        if len(str(y1Temp)) == 1 :
            y1Temp = '0'+str(y1Temp)
            
            
        yearList1.append(str(y1Temp))
        
        if typeIn == 'Timing' or typeIn == 'Box' or typeIn == 'Fly':
            

            if futuresContractDictIn[contractIn1]['num'] <= futuresContractDictIn[contractIn2]['num'] :
                
                y2Temp = i    
                
            else :
                
                y2Temp = i+1
                
                
            if len(str(y2Temp)) ==1 :
                y2Temp = '0'+str(y2Temp)
                
            yearList2.append(str(y2Temp))
            
        elif typeIn =='Crack' or typeIn == 'Location' or typeIn == 'CrossProduct'or typeIn == 'Arb':
            
            y2Temp = i
            
            if len(str(y2Temp)) ==1 :
                y2Temp = '0'+str(y2Temp)
                
            yearList2.append(str(y2Temp))
        
        elif typeIn =='Flat' or typeIn == 'Diff':
            
            yearList2.append(str(y1Temp))
            
        else :
            
            sys.exit('Please Check Type')
        
    return (yearList1,yearList2)

def yearList_Dev(lastTradeIn,yearsBackIn,typeIn,contractIn1,contractIn2,futuresContractDictIn) :
    
    curYearInt = lastTradeIn['Year'] % 100 #Keep only last two digets of yeat
    
    # if contractIn1 == 'F' :
        
    #     curYearInt = int(lastTradeIn[-2:]) +1 #Accounts for Jan being year +1 
        
    # else :
        
    #     curYearInt = int(lastTradeIn[-2:])
    
    yearList1 =[]
    yearList2 = []
    
        
    for i in range(curYearInt - yearsBackIn,curYearInt+1) :
        
        y1Temp = i
        
        if len(str(y1Temp)) == 1 :
            y1Temp = '0'+str(y1Temp)
            
            
        yearList1.append(str(y1Temp))
        
        # if typeIn == 'Timing' or typeIn == 'Box' or typeIn == 'Fly':
            

        if futuresContractDictIn[contractIn1]['num'] <= futuresContractDictIn[contractIn2]['num'] :
            
            y2Temp = i    
            
        else :
            
            y2Temp = i+1
            
            
        if len(str(y2Temp)) ==1 :
            y2Temp = '0'+str(y2Temp)
            
        yearList2.append(str(y2Temp))
            
        # elif typeIn =='Crack' or typeIn == 'Location' or typeIn == 'CrossProduct':
            
        #     y2Temp = i
            
        #     if len(str(y2Temp)) ==1 :
        #         y2Temp = '0'+str(y2Temp)
                
        #     yearList2.append(str(y2Temp))
        
        # else :
            
        #     sys.exit('Please Check Type')
        
    return (yearList1,yearList2)




def createSpread(priceIn1,priceIn2,lastTradeIn,yearListIn1,converstionFactorIn1,converstionFactorIn2,tradeTypeIn):
    
    listNameOut = []
    
    lastTrade = dt.strptime(lastTradeIn['LastTrade'],'%m/%d/%y')
    
    startD = (lastTrade - timedelta(weeks = 53)).strftime('%m/%d/%Y')
    endD = lastTrade.strftime('%m/%d/%Y')
    
    
    df_index = pd.date_range(start =startD, end = endD, freq = 'B' ).rename('Dates')
    spread = pd.DataFrame({}, index = df_index)
    
    price1List = [*priceIn1] # Easy way to make list out of Dict Keys 
    price2List = [*priceIn2] 
    
    p1 = priceIn1[price1List[-1]]['Close']*converstionFactorIn1
    
    if tradeTypeIn == 'Flat' or tradeTypeIn == 'Diff' :
        p2 = priceIn2[price2List[-1]]['Close']*0
    else :
        p2 = priceIn2[price2List[-1]]['Close']*converstionFactorIn2
    spread_temp = pd.merge(p1,p2, how = 'inner', left_index = True, right_index = True)
    spread_temp['spread'] = spread_temp.iloc[:,0] - spread_temp.iloc[:,1]
    spread_temp = spread_temp.iloc[:,2]
    spread_temp = spread_temp[startD:]
    spread = pd.merge(spread,spread_temp,how = 'outer', left_index = True, right_index = True).ffill()
    spread[spread.index > spread_temp.index[-1]] =np.nan
    
    listNameOut.append(yearListIn1[-1])
    
    
    for i,j,m in zip(price1List[:-1],price2List[:-1],yearListIn1[:-1]):
        
        p1 = priceIn1[i]['Close']*converstionFactorIn1
        
        if tradeTypeIn == 'Flat' or tradeTypeIn == 'Diff' :
            p2 = priceIn2[j]['Close']*0
        else :
            p2 = priceIn2[j]['Close']*converstionFactorIn2
        
        spread_temp = pd.merge(p1,p2, how = 'inner', left_index = True, right_index = True)
        spread_temp['spread'] = spread_temp.iloc[:,0] - spread_temp.iloc[:,1]
        
        startD_temp = (spread_temp.index[0] - timedelta(weeks = 52)).strftime('%m/%d/%Y')
        endD_temp = spread_temp.index[-1].strftime('%m/%d/%Y')
        df_indexTemp = pd.date_range(start =startD_temp, end = endD_temp, freq = 'B' ).rename('Dates')
        spreadTemp_df = pd.DataFrame({}, index = df_indexTemp)
        
        spread_temp1 = pd.merge(spreadTemp_df,spread_temp['spread'], how ='outer', left_index = True, right_index = True).ffill()
        
        index_len = len(spread)
        spread_temp2 = pd.DataFrame(spread_temp1.iloc[-index_len:,:])
        spread_temp2 = spread_temp2.set_index(spread.index)
        spread_temp2.columns = [j]
        spread = pd.merge(spread_temp2,spread,how = 'outer', left_index = True, right_index = True)
        listNameOut.append(m)
    
    listNameOut.reverse() # Correcting order of list names 
    spread.columns = listNameOut
    
    return spread


def createSpread_v100(priceIn1,priceIn2,expireScheduleIn,contractIn,yearListIn1,converstionFactorIn1,converstionFactorIn2,tradeTypeIn):
    
    listNameOut = []
    lastTradeIn = contractMonths(expireScheduleIn,contractIn) 
    
    lastTrade = dt.strptime(lastTradeIn['LastTrade'],'%m/%d/%y')
    
    startD = (lastTrade - timedelta(weeks = 53)).strftime('%m/%d/%Y')
    endD = lastTrade.strftime('%m/%d/%Y')
    
    
    df_index = pd.date_range(start =startD, end = endD, freq = 'B' ).rename('Dates')
    spread = pd.DataFrame({}, index = df_index)
    
    price1List = [*priceIn1] # Easy way to make list out of Dict Keys 
    price2List = [*priceIn2] 
    
    p1 = priceIn1[price1List[-1]]['Close']*converstionFactorIn1
    
    if tradeTypeIn == 'Flat' or tradeTypeIn == 'Diff' :
        p2 = priceIn2[price2List[-1]]['Close']*0
    else :
        p2 = priceIn2[price2List[-1]]['Close']*converstionFactorIn2
    spread_temp = pd.merge(p1,p2, how = 'inner', left_index = True, right_index = True)
    spread_temp['spread'] = spread_temp.iloc[:,0] - spread_temp.iloc[:,1]
    spread_temp = spread_temp.iloc[:,2]
    spread_temp = spread_temp[startD:]
    spread = pd.merge(spread,spread_temp,how = 'outer', left_index = True, right_index = True).ffill()
    spread[spread.index > spread_temp.index[-1]] =np.nan
    
    listNameOut.append(yearListIn1[-1])
    
    
    for i,j,m in zip(price1List[:-1],price2List[:-1],yearListIn1[:-1]):
        
        tempYear = int('20' + m)   # CAUTION, THIS WILL ONLY WORK IN TH 2000s (FIX LATER)
        tempLastTrade = dt.strptime(expireScheduleIn[(expireScheduleIn['MonthCode']==contractIn) & (expireScheduleIn['Year']== tempYear)]['LastTrade'][0],'%m/%d/%y')
        
        p1 = priceIn1[i]['Close']*converstionFactorIn1
        
        if tradeTypeIn == 'Flat' or tradeTypeIn == 'Diff' :
            p2 = priceIn2[j]['Close']*0
        else :
            p2 = priceIn2[j]['Close']*converstionFactorIn2
        
        spread_temp = pd.merge(p1,p2, how = 'inner', left_index = True, right_index = True)
        spread_temp['spread'] = spread_temp.iloc[:,0] - spread_temp.iloc[:,1]
        spread_temp = spread_temp[:tempLastTrade].copy()
        
        startD_temp = (spread_temp.index[0] - timedelta(weeks = 52)).strftime('%m/%d/%Y')
        endD_temp = spread_temp.index[-1].strftime('%m/%d/%Y')
        df_indexTemp = pd.date_range(start =startD_temp, end = endD_temp, freq = 'B' ).rename('Dates')
        spreadTemp_df = pd.DataFrame({}, index = df_indexTemp)
        
        spread_temp1 = pd.merge(spreadTemp_df,spread_temp['spread'], how ='outer', left_index = True, right_index = True).ffill()
        
        index_len = len(spread)
        spread_temp2 = pd.DataFrame(spread_temp1.iloc[-index_len:,:])
        spread_temp2 = spread_temp2.set_index(spread.index)
        spread_temp2.columns = [j]
        spread = pd.merge(spread_temp2,spread,how = 'outer', left_index = True, right_index = True)
        listNameOut.append(m)
    
    listNameOut.reverse() # Correcting order of list names 
    spread.columns = listNameOut
    
    return spread
