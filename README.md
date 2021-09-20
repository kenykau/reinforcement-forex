# reinforcement-forex
## *disclaimer*
Forex and CFD trading is extremely risky. All materials provided in this repository is only for learning and analysis purpose. It is your own risk taking the code in live trading.

## introduction
I have been looking for the reinforcement learning environment for leveraged forex trading or CFD trading for a while. I found that there are a lot of environment's for stocks and crypto(es). 
like [gym-anytrading](https://github.com/AminHP/gym-anytrading) or [tensortrade.org](https://github.com/tensortrade-org/tensortrade). Forex trading has slightly differences from those environment.


1. The profit and loss formula is different. It requires to convert back and forth to get the pnl into the account currency, which means we might need an extract data set (i.e. if you trading EURGBP and your account currency is USD, you need extract data pair for GBPUSD).
2. There is a swap terms in leveraged trading. We need to keep track of the swap expense if the trade is long lasting for more than 1 day
3. It also needs to compute the margin requirement before an order is successfully executed or order(s) might forcely required to close.

I am new to reinforcement learning and python. Therefore, I would like to invite anyone who interesting in leveraged forex trading to develope a better gym env for the community.

## details
Inspired by tensor trade, I divided the env into few parts as follow:
1. Broker - Broker class mainly serves as the data provider, which stores the data of 28 pairs trading currencies.
2. Instructment - The tradable pairs class, which stores the pair attributes like digits, swap charges, lotsize and etc
3. Order - The trade class stores the trade information of a particular trade during the trading cycle like openprice, closeprice, floating loss, floating profit, marginhold
4. Account - The account class stores all trades during the whole training account life cycle, like the number of trades, marginhold, equity, balance and trade history.
5. FxEnv - The gym env for forex trading
6. Stable-Baselines3 - Which is required for simplier RL implementataion
7. You can trade the main.py the test it.

## code sample
```python
    #define a broker
    broker: Broker = Broker()
    
    #define a symbol
    eurusd: Symbol = Symbol(broker, "EURUSD")
    
    #define a gym env
    fx: FxEnv = FxEnv(broker=broker, symbol=eurusd, window_size=4)

    #convert the gym env to stable-baselines3 DummyVecEnv
    ec.check_env(fx)
    env_creator = lambda: fx
    env = DummyVecEnv(env_fns=[env_creator])
    
    #define the model and train
    model = A2C("MlpPolicy", env)
    model.learn(total_timesteps=10000)
    model.save('eurusd_a2c')
```

## What I found
1.  Commission, Spread, Swap will eat your profit completely. I used H1 data to test, most of the training is stop out (I set 50% of initial a/c balance). 
2.  Next, I set all commission, spread, swap to 0, profit making :), but
3.  The training process try to perform Holding Action all the time. This might related to reward schema. I hope later on I can resolve this problem. 

## To do
1.  Use larger time frame to test
2.  Use different model to test
3.  Documentation
4.  Use different reward schema
5.  Resolve the Holding performance (no more exploration)
