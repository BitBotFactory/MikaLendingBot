#Poloniex lending bot

Poloniex lending bot is written in Python for automatic lending on Poloniex exchange.
It will lend automatically all cryptocurrencies found in your lending account.

It uses an advanced lending strategy which will spread offers across the lend book to take advantage of possible spikes in lending rates. Inspired by [MarginBot](https://github.com/HFenter/MarginBot) and [BitfinexLendingBot](https://github.com/eAndrius/BitfinexLendingBot).

##Install
```
git clone https://github.com/Mikadily/poloniexlendingbot
cd poloniexlendingbot/
python marginbot.py
```

##Configuration

When you first run the script a default.cnf will be generated. Edit it with your apikey and secret values.

```
[API]
apikey = YourAPIKey
secret = YourSecret

[BOT]
#sleep between iterations, time in seconds
sleeptime = 60

#minimum daily lend rate in percent
mindailyrate = 0.04

#max rate. 2% is good choice because it's default at margin trader interface.
#5% is max to be accepted by the exchange
maxdailyrate = 2

#The number of offers to split the available balance across the [gaptop, gapbottom] range.
spreadlend = 3

#The depth of lendbook (in percent of lendable balance) to move through
#before placing the first (gapbottom) and last (gaptop) offer.
#If gapbottom is set to 0, the first offer will be at the lowest possible rate.
#However some low value is recommended (say 10%) to skip dust offers.
gapbottom = 10
gaptop = 200

#Daily lend rate threshold after which we offer lends for 60 days as opposed to 2.
#If set to 0 all offers will be placed for a 2 day period
sixtydaythreshold = 0.2
```

If `spreadlend = 1` and `gapbottom = 0`, it will behave as simple lending bot lending at lowest possible value.

##Donations

If you find it useful, please consider donating some bitcoins: 1MikadW4iKTJ54GVrj7xS1SrZAhLUyZk38

