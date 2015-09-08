#Poloniex lending bot

Poloniex lending bot is written in Python for automatic lending on Poloniex exchange.
It will lend automatically all cryptocurrencies found in your lending account.

It uses an advanced lending strategy which will spread offers across the lend book to take advantage of possible spikes in lending rates. Inspired by [MarginBot](https://github.com/HFenter/MarginBot) and [BitfinexLendingBot](https://github.com/eAndrius/BitfinexLendingBot).

##Install
###Linux
```
git clone https://github.com/Mikadily/poloniexlendingbot
cd poloniexlendingbot/
python lendingbot.py
```
When you first run the script a default.cnf will be generated. Edit it with your apikey and secret values.

###Windows
1. Install poloniexlendingbot - go to https://github.com/Mikadily/poloniexlendingbot and click the "Download Zip" button on the right. Unzip it into any location you choose.
2. Install Python from https://www.python.org/ftp/python/2.7.10/python-2.7.10.msi . Run the executable. Choose to install the feature Add python.exe to Path on local hard drive during installation; Python should then be installed in C:\Python27
3. Check that Python runs. Open a new command prompt as administrator by typing cmd.exe into the Start menu and pressing Ctrl+Shift+Enter. Type python and you should see something like: `Python 2.7.10 (default....`
4. Go to location where you unzipped the bot and double click (run) lendingbot.py. It will run briefly and generate default.cfg. Open it with your favorite editor, replace YourAPIKey and YourSecret with one's you generated on Poloniex.

5. Double click (run) lendingbot.py again. Off you go!

##Configuration

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

#custom config per coin, useful when closing positions etc.
#syntax: ["COIN:mindailyrate:maxactiveamount",...]
#if maxactive amount is 0 - stop lending this coin. in the future you'll be able to limit amount to be lent.
#coinconfig = ["BTC:0.18:1","CLAM:0.6:1"]
```

If `spreadlend = 1` and `gapbottom = 0`, it will behave as simple lending bot lending at lowest possible offer.

##Donations

If you find it useful, please consider donating some bitcoins: 1MikadW4iKTJ54GVrj7xS1SrZAhLUyZk38

