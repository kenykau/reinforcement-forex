# reinforcement-forex

I have been looking for the reinforcement learning environment for leveraged forex trading for a while. I found that there are a lot of environment's for stocks and crypto(es). 
like [gym-anytrading](https://github.com/AminHP/gym-anytrading) or [tensortrade.org](https://github.com/tensortrade-org/tensortrade).Forex trading has slightly differences from those environment.


1. The profit and loss formula is different. It requires to convert back and forth to get the pnl into the account currency, which means we might need an extract data set (i.e. if you trading EURGBP and your account currency is USD, you need extract data pair for GBPUSD).
2. There is a swap terms in leveraged trading. We need to keep track of the swap expense if the trade is long lasting for more than 1 day
3. It also needs to compute the margin requirement before an order is successfully executed or order(s) might forcely required to close.

I am new to reinforcement learning and python. Therefore, I would like to invite anyone who interesting in leveraged forex trading to develope a better gym env for the community.

## details
Inspired by tensor trade, I divided the env into few parts as follow:
1. Broker - Broker class mainly serves as the data provider, which stores the data of 28 pairs trading currencies.
2. Instructment - The tradable pairs class, which stores the pair attributes like digits, swap charges, lotsize and etc
3. Trade - The trade class stores the trade information of a particular trade during the trading cycle like openprice, closeprice, floating loss, floating profit, marginhold
4. Account - The account class stores all trades during the whole training account life cycle, like the number of trades, marginhold, equity, balance and trade history.

## code sample
    #first define a Broker instance
    broker = Broker(data_file='data_file.csv', currency='USD')
    
    #then, define an Account instance
    account = Account(broker, initial_balance=10000, stop_out=0.1)
