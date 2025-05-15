# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 13:22:27 2022

@author: raulrivera
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import sys
from GvWSConnection import *

def backwardAdjPrices_v200(dfIn,expireDatesIN,rollDaysIn) :
    
    dfIn.columns = ['PriceA','PriceB']
    expireDatesIn = expireDatesIN.copy()
    expireDatesIn['expireVec'] = 1
    # expireDatesLong = pd.DataFrame({},index = dfIn.index
    expireDatesLong = pd.DataFrame({},index = pd.bdate_range(start = expireDatesIn.index[0], end = expireDatesIn.index[-1]))
    ex_df = pd.merge(expireDatesIn,expireDatesLong, how = 'outer', left_index = True, right_index = True)
   
    ex_df['rollDays'] = 0
    ex_df['rollAdj'] = 0
    ex_List = ex_df['LastTrade'].bfill()
    
    for ex in ex_List :
        

        hh =  ex_df[ex_df['LastTrade']==ex]
        locE =  ex_df.index.get_loc(hh.iloc[0].name)
        ex_df.iloc[locE-rollDaysIn+1:locE+1,ex_df.columns.get_loc('rollDays')] = 1
    
    df = pd.merge(dfIn,ex_df, how = 'inner',left_index = True, right_index = True)
    
    initialState = df.iloc[0,df.columns.get_loc('rollDays')] 

    for rl in range(1,len(df)) :
        
        state = df.iloc[rl,df.columns.get_loc('rollDays')]
        
        if (state == 1) & (initialState == 0) :
            
            df.iloc[rl,df.columns.get_loc('rollAdj')] =  df.iloc[rl,df.columns.get_loc('PriceA')] - df.iloc[rl,df.columns.get_loc('PriceB')]
            initialState = 1
            
        elif (state == 0) & (initialState == 1) :
            
            initialState = 0
    # df['rollAdjShift'] = df['rollAdj'].shift(-1)
    # df['rollAdjShift'].fillna(0,inplace = True)
    df['cumRoll'] = df['rollAdj'].sort_index(ascending = False).cumsum().sort_index()
    df['PriceAdj'] = df.apply(lambda row : row['PriceB'] if row['rollDays'] == 1 else row['PriceA'], axis = 1)
    df['Price_BA'] = df['PriceA']  - df['cumRoll'] 
    
    return df


def backwardAdjPrices_v201(dfIn,expireDatesIN,rollDaysIn) :
    
    dfIn.columns = ['PriceA','PriceB']

    expireDatesIn = expireDatesIN.copy()

    expireDatesLong = pd.DataFrame({},index = pd.bdate_range(start = expireDatesIn.index[0], end = expireDatesIn.index[-1]))
    ex_df = pd.merge(expireDatesIn,expireDatesLong, how = 'outer', left_index = True, right_index = True)
       
    ex_df['rollDays'] = 0
    ex_df['rollAdj'] = 0
    ex_List = ex_df['LastTrade'].bfill()

    for ex in ex_List :
        
        hh =  ex_df[ex_df['LastTrade']==ex]
        locE =  ex_df.index.get_loc(hh.iloc[0].name)
        ex_df.iloc[locE-rollDaysIn:locE+1,ex_df.columns.get_loc('rollDays')] = 1
        
        
        
    df = pd.merge(dfIn,ex_df, how = 'inner',left_index = True, right_index = True)

    initialState = df.iloc[0,df.columns.get_loc('rollDays')] 

    for rl in range(1,len(df)) :
        
        state = df.iloc[rl,df.columns.get_loc('rollDays')]
        
        if (state == 1) & (initialState == 0) :
            
            df.iloc[rl,df.columns.get_loc('rollAdj')] =  df.iloc[rl,df.columns.get_loc('PriceB')] - df.iloc[rl,df.columns.get_loc('PriceA')]
            initialState = 1
            
        elif (state == 0) & (initialState == 1) :
            
            initialState = 0    
            
            
    df['rollAdj'] = df['rollAdj'].shift(-1).fillna(0)
    df['cumRoll'] = df['rollAdj'].sort_index(ascending = False).cumsum().sort_index()
    df['PriceAdj'] = df.apply(lambda row : row['PriceB'] if row['rollDays'] == 1 else row['PriceA'], axis = 1)    
    df['Price_BA'] = df['PriceAdj']  +  df['cumRoll']  
    
    
    return df


def createDailyDataMV(result, contractListIn,nameIn, start_column=0) :
    # This function takes the time series object from Market View and returns a dict of prices 
    colNames = result[0].field_names[start_column:]
    
    dfOut = pd.DataFrame({})
    dictOut = {}
    table = []
    strList = []
    index = []
    for row in result:
        
        values = list(row.values())
        # str_values = [str(x) for x in values[start_column:]]
        
        index.append(values[1].replace(hour=0)) # Setting Hour to 0 instead of 12
        table.append(values[2:])
        strList.append(values[:2])
            
            
    # indexIn = index.replace(hour=0)
    df1 = pd.DataFrame(table, index = index)
    df2 = pd.DataFrame(strList, index = index)
    df = pd.concat([df2,df1],axis = 1)
    
    df.columns = colNames
    df.drop(columns = ['TradeDateTimeUtc'],inplace = True)
    
    
    # nameList =  df['PriceSymbol'].unique()
    # nameList =  df['PriceSymbol'] # Does this need to be unique
    nameList = contractListIn
    if len(nameList) != len(nameIn) :
        
        # print('Length of Name List Do Not Match')
        
        sys.exit('Length of Name List Do Not Match')
        
    for i,j in zip(nameList,nameIn) :
        
        tempOut = df[df['PriceSymbol']==i].copy()
        tempOut['Name'] = j
        dfOut = pd.concat([dfOut,tempOut['Close'].rename(j)], axis = 1)
        
        dictOut.update({j:tempOut})
        
    return dictOut 


def createForwardCurveMV(result,start_column=0) :
    # This function takes the time series object from Market View and returns a dict of prices 
    colNames = result[0].field_names[start_column:]
    
    dictOut = {}
    table = []
    strList = []
    index = []
    for row in result:
        values = list(row.values())
        # str_values = [str(x) for x in values[start_column:]]
        table.append(values[2:])
        index.append(values[1].replace(hour=0)) # Setting Hour to 0 instead of 12
        strList.append(values[:2])
        
    # indexIn = index.replace(hour=0)
    df1 = pd.DataFrame(table, index = index)
    df2 = pd.DataFrame(strList, index = index)
    df = pd.concat([df2,df1],axis = 1)
    
    df.columns = colNames
    df.drop(columns = ['TradeDateTimeUtc'],inplace = True)

    return df


def rollYield(dataIn) :
    dataLog = np.log(dataIn)
    yield_roll = []
    for i in range(0,len(dataLog)) :
        
        Y = dataLog.iloc[i,:]
        x = np.arange(1,len(Y)+1)
        X = sm.add_constant(x)
        results = sm.OLS(Y,X).fit()
        yield_roll.append(results.params[1]*-12)
        
    df = pd.DataFrame(yield_roll, index = dataLog.index, columns = ['rollYield']) 
        
    dataOut = pd.merge(dataIn, df, how = 'inner', left_index = True, right_index = True)
    
    return dataOut

def priceDataSetCreateBB(dictIn,itemsIn,startDateIn,endDateIn) :
    
    from blp import blp
    bquery = blp.BlpQuery().start()

    price_df = pd.DataFrame({})

    for i,j in zip(list(dictIn.values()),list(dictIn.keys())) : 
         
        data = bquery.bdh(i[0],itemsIn,start_date=startDateIn,end_date=endDateIn)
        data[j] = data['PX_SETTLE']
        data.set_index('date', inplace = True)

        
        price_df = pd.concat([price_df,data[j]], axis = 1)
        

    price_df.sort_index(inplace = True)
    
    return price_df

def priceDataSetCreateMV(priceDictIn,startDateIn) :
    
    USERNAME = 'GCC018'
    PASSWORD = 'password'
    
    conn = GvWSConnection(USERNAME, PASSWORD)
    d1 = conn.get_daily(list(priceDictIn.values()), start_date = startDateIn)
    
    dictOut = createDailyDataMV(d1,list(priceDictIn.values()),list(priceDictIn.keys()))
    
    return dictOut 