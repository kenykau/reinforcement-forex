from typing import List, Dict
import pandas as pd

class Broker:
    def __init__(self, name='broker1') -> None:
        '''
        Broker class constructor, broker name can be provided to distingish different brokers
        '''
        self.name:str = name          #name of the broker
        self.symbols:List[str] = []   #symbols of the broker's tradable assets
        self.data:List[Dict] = []     #a list of data of the symbol
        self.shift:int = 0            #the position pointer of the data

    def data_processing(self, datafile:str='', fields:Dict={
            'symbol':'symbol',
            'tf':'timeframe',
            'dt':'dt',
            'o':'open',
            'h':'high',
            'l':'low',
            'c':'close',
            'v':'volume',
            'b':'bid',
            'a':'ask'})->None:
        '''
        The history data loading of all symbols for the broker
        The fields parameters provide a way to convert raw data fields to system-wise fields, do not change the key but value of each field in the Dict object to fit the data
        '''
        assert len(datafile)>0, 'datafile is empty'
        
        df = pd.read_csv(datafile, 
            header=0, 
            parse_dates=[fields['dt']], 
            index_col=fields['dt'],
            infer_datetime_format=True)
        
        #get all symbols from the csv file
        self.symbols = df['symbol'].unique().tolist()
        
        #convert csv field name to system-wise field name
        map_fields = {v:k for k,v in fields.items()}
        df.rename(columns=map_fields, inplace=True)

        #the datetime index pointer
        self.dt :pd.DatetimeIndex = df.index.unique().copy()
        
        #separating symbols data from raw data to the list
        for pair in self.symbols:
            #append the details of each symbol to data
            self.data.append({
                'symbol':pair,
                'raw': df[df['symbol']==pair].copy()})
            
            #alignment of index
            self.dt = self.dt.drop(self.dt.difference(self.data[-1]['raw'].index).to_list())
        
        #alignment of the data
        for i in range(len(self.data)):
            #alignment of index
            self.data[i]['raw'] = self.data[i]['raw'].reindex(self.dt)
            #alignment of columns
            self.data[i]['raw'].rename(columns=map_fields, inplace=True)
            #alignment of index
            self.data[i]['raw'].index = self.dt
            
    def move(self, shift:int=-1)->None:
        '''
        move provides the way of moving the pointer to next bar if shift=-1, if shift>=0, the pointer will move to the desire position
        '''
        assert shift<len(self.dt), 'shift is too large'
        if shift>=0:
            self.shift = shift
        else:
            self.shift += 1
    
    def get_data(self, symbol:str, shift:int =-1, window_size:int=0)->pd.DataFrame:
        '''
        Get data of a specific symbol
        shift:int, the shift of the data, if -1, return the data of the current shift
        window_size:int, the size of the window, if 0, return all the data of the symbol, if greater than 0, return the data of the window_size starting shift - window_size. Make sure the window_size is smaller than the current shift and the input shift
        '''
        
        assert len(self.data)>0, 'data is empty'
        assert symbol in self.symbols, 'symbol is not in symbol list'     
        assert shift<len(self.dt), 'shift is not valid'
        assert (window_size<=self.shift or window_size<shift) and window_size>=0, 'window_size is not valid'

        if shift == -1:
            shift = self.shift

        if window_size == 0:
            return self.data[self.symbols.index(symbol)]['raw'].copy()
        
        if window_size > 0:
            return self.data[self.symbols.index(symbol)]['raw'].iloc[shift-window_size:shift].copy()

    def get_rate(self, symbol:str)->pd.Series:
        '''
        Get the rate of a specific symbol
        '''
        assert len(self.data)>0, 'data is empty'
        assert symbol in self.symbols, 'symbol is not in symbol list'
        return self.data[self.symbols.index(symbol)]['raw'].iloc[self.shift]

    def add_feature(self, symbol:str, feature:pd.Series, feature_name:str='')->None:
        '''
        Add a feature to the data of a specific symbol
        '''
        assert len(self.data)>0, 'data is empty'
        assert symbol in self.symbols, 'symbol is not in symbol list'
        assert len(feature)==len(self.data[self.symbols.index(symbol)]['raw']), 'feature size is not equal to the raw data size'
        if feature_name == '':
            feature_name = 'feature'
        self.data[self.symbols.index(symbol)][feature_name] = feature
