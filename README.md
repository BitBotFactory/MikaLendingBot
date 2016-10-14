#Poloniex lending bot <img src="https://nevet.me/public/icon.png" width="50">

Poloniex lending bot is written in Python for automatic lending on Poloniex exchange.
It will lend automatically all cryptocurrencies found in your lending account.

It uses an advanced lending strategy which will spread offers across the lend book to take advantage of possible spikes in lending rates. Inspired by [MarginBot](https://github.com/HFenter/MarginBot) and [BitfinexLendingBot](https://github.com/eAndrius/BitfinexLendingBot).

[![Join the chat at https://gitter.im/Mikadily/poloniexlendingbot](https://badges.gitter.im/Mikadily/poloniexlendingbot.svg)](https://gitter.im/Mikadily/poloniexlendingbot?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Click the chart to see our workflow management with Waffle.io
[![Throughput Graph](https://graphs.waffle.io/Mikadily/poloniexlendingbot/throughput.svg)](https://waffle.io/Mikadily/poloniexlendingbot/)

##Documentation
[Click here to read the Documentation, hosted by readthedocs.io](http://poloniexlendingbot.readthedocs.io/en/latest/index.html)


### Command Line Parameters
[View Arguments Documentation in the Wiki](https://github.com/Mikadily/poloniexlendingbot/wiki/Arguments)


### Bot Status Webpage
Under www folder you can find lendingbot.html webpage, it can be used to parse the json output file.
- currently javascript expects 'botlog.json' file to be in the same folder i.e. jsonfile = www\botlog.json (or webserver folder)
- will refresh every 30sec
- events log is presented in reverse order - last is on top
- uncomment startWebServer = true if you need a webserver for viewing, this will start a simple webserver.

##Donations

If you find it useful, please consider donating some bitcoins: 37VoSLbiqVWGDA5Y8rmo5XaQxPo551gBY8
This address goes to a Multisig wallet with keys held by Mikadily, rnevet, and Evanito. 
