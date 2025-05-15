 # -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 11:33:54 2022

@author: raulrivera
"""

from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import timedelta, datetime as dt
from SeasonalPriceUtilities import *
import seaborn as sns
import os
import pickle 

import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

from sqlalchemy import create_engine, text
from urllib import parse

#%% Reference Locations
#locB = r'C:\Users\GCC_Admin\Sullivan Dropbox\Raul Rivera\GCC\00-Dashboard'
locB = r'C:\Users\RaulRivera.AzureAD\Sullivan Dropbox\Raul Rivera\GCC\00-Dashboard'


loc_Ref = r'Reference_Data'
loc_List = r'Seasonal_Process'
loc_Exp = r'Expire_Schedule'
loc_Output = r'Prices'
loc_Output_1 = r'SeasonalCharts'


#%% Database Info

schemaName = 'Reference'
table_Name = 'FuturesExpire'


# Connection parameters for SQL Server
connection_params = {
    "server": "tcp:gcc-db-v100.database.windows.net,1433",
    "database": "GCC-db-100",
    "username": "rrivera",
    "password": "Mistymutt_1",
}

connecting_string = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server={connection_params['server']};"
    f"Database={connection_params['database']};"
    f"Uid={connection_params['username']};"
    f"Pwd={connection_params['password']};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

params = parse.quote_plus(connecting_string)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}",fast_executemany=True)

#%% Expire Schedule 
futuresContractDict= {'F':{'abr':'Jan','num':1},'G':{'abr':'Feb','num':2},'H':{'abr':'Mar','num':3},'J':{'abr':'Apr','num':4},
                      'K':{'abr':'May','num':5},'M':{'abr':'Jun','num':6},'N':{'abr':'Jul','num':7},'Q':{'abr':'Aug','num':8},
                      'U':{'abr':'Sep','num':9},'V':{'abr':'Oct','num':10},'X':{'abr':'Nov','num':11},'Z':{'abr':'Dec','num':12}}

query = "SELECT * FROM [Reference].[FuturesExpire]" 

expire = pd.read_sql(query,con=engine)




# #%% Expire Schedule 
# futuresContractDict= {'F':{'abr':'Jan','num':1},'G':{'abr':'Feb','num':2},'H':{'abr':'Mar','num':3},'J':{'abr':'Apr','num':4},
#                       'K':{'abr':'May','num':5},'M':{'abr':'Jun','num':6},'N':{'abr':'Jul','num':7},'Q':{'abr':'Aug','num':8},
#                       'U':{'abr':'Sep','num':9},'V':{'abr':'Oct','num':10},'X':{'abr':'Nov','num':11},'Z':{'abr':'Dec','num':12}}

# # fileInExpire = 'ExpireTable.pickle'

# # expiretableName = os.path.join(locB,loc_Ref,loc_Exp,fileInExpire)
# # expireIn = open(expiretableName,'rb')
# # expire = pickle.load(expireIn)
# # expireIn.close()

# fileInExpire = 'ExpireTable.pickle'

# expire = pd.read_pickle(os.path.join(locB,loc_Ref,loc_Exp,fileInExpire))

#%% Contract Lists 

fileInList = 'FuturesProcessList_mini.csv'
processList = pd.read_csv(fileInList)#pd.read_csv(os.path.join(locB,loc_Ref,loc_List,fileInList))

#%%
for i in range(0,len(processList)) :
    
    print(i)
    tempProcess = processList.iloc[i,:]
    
    tempExpire = expire[expire['Ticker']==tempProcess['ExpireFlag']]
    # tempExpire.set_index(pd.to_datetime(tempExpire['LastTrade']), inplace = True)
    tempExpire.set_index(pd.to_datetime(tempExpire['LastTrade'], format='%m/%d/%y'), inplace = True)
    
    
    # print(tempProcess)
    
    tradeType = tempProcess['Type']
    locationOut = tempProcess['LocationOut']
    contractIn_1 = tempProcess['Contract_1']
    contractIn_2 = tempProcess['Contract_2']
    yearsBack = tempProcess['YearsBack']
    converstionFactor1 = tempProcess['ConversionFactor_1']
    converstionFactor2 = tempProcess['ConversionFactor_2']
    
    lastTrade = contractMonths(tempExpire,contractIn_1)
    # lastTrade = contractMonths(tempExpire,contractIn_2) 
    
    # print(lastTrade)
    yearList1,yearList2 = yearList(lastTrade,yearsBack,tradeType,contractIn_1,contractIn_2,futuresContractDict)
    if i == 25 :
        
        print('k')
        
    if  tradeType =='Flat' or tradeType =='Diff':
        zz1 = getSeasonalPrices(tempProcess['SeriesName_1'],tempProcess['NameOut_1'],contractIn_1,yearList1)
        zz2 = zz1
        spread = createSpread(zz1,zz2,lastTrade,yearList1,converstionFactor1,converstionFactor2,tradeType)
        # spread = createSpread_v100(zz1,zz2,lastTrade,yearList1,converstionFactor1,converstionFactor2,tradeType)
        
    else :
        zz1 = getSeasonalPrices(tempProcess['SeriesName_1'],tempProcess['NameOut_1'],contractIn_1,yearList1)
        zz2 = getSeasonalPrices(tempProcess['SeriesName_2'],tempProcess['NameOut_2'],contractIn_2,yearList2)
        spread = createSpread(zz1,zz2,lastTrade,yearList1,converstionFactor1,converstionFactor2,tradeType)
        # spread = createSpread_v100(zz1,zz2,tempExpire,contractIn_1,yearList1,converstionFactor1,converstionFactor2,tradeType)
        
    if tradeType =='Box' or tradeType =='Fly' :
        
        
        
        contractIn_3 = tempProcess['Contract_3']
        contractIn_4 = tempProcess['Contract_4']
        converstionFactor3 = tempProcess['ConversionFactor_3']
        converstionFactor4 = tempProcess['ConversionFactor_4']
        
        yearList1a,yearList3 = yearList(lastTrade,yearsBack,tradeType,contractIn_1,contractIn_3,futuresContractDict)
        yearList1b,yearList4 = yearList(lastTrade,yearsBack,tradeType,contractIn_1,contractIn_4,futuresContractDict)
        
        zz3 = getSeasonalPrices(tempProcess['SeriesName_3'],tempProcess['NameOut_3'],contractIn_3,yearList3)
        zz4 = getSeasonalPrices(tempProcess['SeriesName_4'],tempProcess['NameOut_4'],contractIn_4,yearList4)
        
        spread1 = spread.copy()
        # spread2 = createSpread(zz3,zz4,lastTrade,yearList1,converstionFactor3,converstionFactor4,tradeType)
        spread2 = createSpread_v100(zz3,zz4,tempExpire,contractIn_1,yearList1,converstionFactor3,converstionFactor4,tradeType)
        spread = spread1 - spread2
        
    spreadVol = spread.diff().rolling(20).std()*2
    
    fig = make_subplots(rows=2,subplot_titles=("Seasonal Price Evolution", "Var/Unit"))
    
    
    for j in yearList1[:-1]:
    
        fig.add_trace(go.Scatter(x= spread.index, y=spread[j], name= '20'+str(j) + ' Year',
                              line=dict(width=2)),row=1, col=1)
        
        fig.add_trace(go.Scatter(x= spreadVol.index, y=spreadVol[j], name= '20'+str(j) + ' Year',
                              line=dict(width=2)),row=2, col=1)
    
    
    fig.add_trace(go.Scatter(x= spread.index, y=spread[yearList1[-1]], name= '20'+ yearList1[-1] + ' Year',
                          line=dict(color = 'black', width=4)),row=1, col=1)
    
    fig.add_trace(go.Scatter(x= spreadVol.index, y=spreadVol[yearList1[-1]], name= '20'+ yearList1[-1] + ' Year',
                          line=dict(color = 'black', width=4)),row=2, col=1)

        
    titleOut = tempProcess['LocationOut'] + tempProcess['Type'] + ' ' +tempProcess['UnitsOut']
        
    fig.update_layout(title= titleOut,
                        xaxis_title ='Date',
                        xaxis = dict(tickfont = dict(size=15)),
                        yaxis_title = tempProcess['UnitsOut'],
                        yaxis = dict(tickfont = dict(size=20)))
    
    
    nameLength = len(pd.DataFrame([tempProcess['NameOut_1'] , tempProcess['NameOut_2'],tempProcess['NameOut_3'],tempProcess['NameOut_4']]).dropna())
    
    if nameLength == 1:
        
        fileNameOut = futuresContractDict[contractIn_1]['abr'] + '_' + tempProcess['NameOut_1'] + '_'+ tempProcess['Type'] +'.html'
    
    elif nameLength == 2 :
        
        fileNameOut = futuresContractDict[contractIn_1]['abr'] + '_' + futuresContractDict[contractIn_2]['abr'] + '_' + tempProcess['NameOut_1'] + '_'  + tempProcess['NameOut_2']  + '_' + tempProcess['Type'] +'.html'
        
    elif nameLength == 4 :
        
        fileNameOut = futuresContractDict[contractIn_1]['abr'] + '_' + futuresContractDict[contractIn_2]['abr'] + '_' + futuresContractDict[contractIn_3]['abr'] + '_' + futuresContractDict[contractIn_4]['abr'] +'_' + tempProcess['NameOut_1'] + '_'+ tempProcess['NameOut_2'] + tempProcess['NameOut_3'] + '_'+ tempProcess['NameOut_4'] + '_' + tempProcess['Type'] +'.html'
    
    #fileNameOut = futuresContractDict[contractIn_1]['abr'] + '_' + tempProcess['NameOut_1'] + '_'+ tempProcess['Type'] +'.html'
    fileLocOut = os.path.join(os.getcwd(), 'sam')
    os.makedirs(fileLocOut, exist_ok=True)

    imageFileOut = os.path.splitext(fileNameOut)[0] + '.png'
    fig.write_image(os.path.join(fileLocOut, imageFileOut), format='png', scale=2)

    
    #fig.write_html(os.path.join(fileLocOut,fileNameOut))
    
    


#%%
# yearFilter = ['17','18','19','20','21','24','25']
# currentValue = spread[yearList1[-1]].dropna()
# # xx = spread.iloc[-60:,[0,2,3,4,5,7,8,10]]
# # xx = spread['2023-04':].copy()
# xx = spread.iloc[-155:-25,:]
# xx = xx.loc[:,yearFilter].copy()
# # xx = spread.iloc[-155:,:]
# # xx = xx.iloc[:,1:].copy()
# ss = xx.stack().reset_index()
# ss.columns = ['aa','bb','cc']
# xxx = ss[['cc']]

# nameOut = ' EW Gas (Mar) (' + contractIn_1 + ' ) :' "{:.2f}".format(spread.iloc[:,-1].dropna()[-1])
# xxx.columns = [nameOut]
# # alue :  ' + "{:.2f}".format(['yport'][-1]) ')
# # xx = dictIn['yport'].rename('Current Value :  ' + "{:.2f}".format(dictIn['yport'][-1]) ')
# # kwargs = {'cumulative': True}
# # sns.distplot(xx, hist_kws=kwargs, kde_kws=kwargs)

# sns.displot(data =xxx[nameOut], bins =25 ,kde =True)

# stack= xx.stack()
# print(stack.describe()) 