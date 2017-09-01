.. _market_analysis-section:

Market Analysis
---------------

Overview
``````````
This feature records a currency's market and allows the bot see trends. With this data, we can compute a recommended minimum lending rate per currency to avoid lending at times when the rate dips.

When this module is enabled it will start recording the lending rates for the market in an sqlite database. This will be seen in the market_data folder for your bot. This supersedes the previous method of storing it in a file. The files can be removed if you have them from older versions of the bot.

There will be a DB created for each currency you wish to record. These can be enabled in the `analyseCurrencies`_ configuration option.  

 .. warning:: The more currencies you record, the more data stored on disk and CPU processing time will be used. You will also not get as frequent results for the currencies, i.e. You may have trouble getting results for your configured ``analyseUpdateInterval`` This is explained further in the `Recording currencies`_ section. 

A quick list of each config option and what they do

========================= =============================================================================================
`analyseCurrencies`_      A list of each currency you wish to record and analyse
`analyseUpdateInterval`_  The frequency between rates requested and stored in the DB
`lendingStyle`_           The percentage used for the percentile calculation
`percentile_seconds`_     The number of seconds to analyse when working out the percentile
`MACD_long_win_seconds`_  The number of seconds to used for the long moving average
`MACD_short_win_seconds`_ The number of seconds to used for the short moving average
`keep_history_seconds`_   The age (in seconds) of the oldest data you wish to keep in the DB
`recorded_levels`_        The depth of the lending book to record in the DB, i.e. how many unfilled loans
`data_tolerance`_         The percentage of data that can be ignore as missing for the time requested in
                          ``percentile_seconds`` and ``MACD_long_win_seconds``
`daily_min_method`_       Which method (MACD or percentile) to use for the daily min calculation
`MACD_multiplier`_        Only valid for MACD method. The figure to scale up the returned rate value from the MACD calculation
`ma_debug_log`_           Print some extra info on what's happening with the rate calculations
========================= =============================================================================================

The module has two main methods to calculate the minimum rate:

Percentile
``````````
This method takes all the data for the given time period (`percentile_seconds`_) and works out the Xth percentile (`lendingStyle`_) for that set of data. For example if you are using a ``lendingStyle`` of 85 and you had a list of rates like so

  :Example: 0.04, 0.04, 0.05, 0.05, 0.05, 0.05, 0.06, 0.06, 0.06, 0.07, 0.07, 0.07, 0.08, 0.08, 0.09, 0.09, 0.09, 0.10, 0.10, 0.10

The 85th percentile would be 0.985 because 85% of rates are below this. The following configuration options should be considered when using the percentile calculation method:-


MACD
````
Moving Average Convergence Divergence, this method using moving averages to work out if it's a good time to lend or not. Currently this is only implemented to limit the minimum daily rate for a currency. This will be changing in the future. 
It by looking at the best rate that is available from the recorded market data for two windows, the long and short window, then taking an average of them both. If the short average is higher than the long average then it considers the market to be in a good place to lend (as the trend for rates is going up) and it will return a `suggested loan rate`_. If the long window is greater than the short window, then we will not lend as trend for rates is below what it should be.
So for example:

===== ===== ==== =========
Time  Short Long Suggested
===== ===== ==== =========
12:00 0.08  0.1  0.1
12:01 0.09  0.1  0.1
12:02 0.1   0.1  0.105
12:03 0.11  0.1  0.1155
12:04 0.12  0.1  0.126
===== ===== ==== =========

In this example, the bot would start to lend at 12:02 and it would suggest a minimum lending rate of 0.1 * `MACD_multiplier`_, which by default is 1.05. Giving a rate of 0.105. This is then passed back to the main lendingbot where it will use your gaptop and gapbottom, along with spreads and all the other smarts to place loan offers.

Currently using this method gives the best results with well configured gaptop and gapbottom. This allows you to catch spikes in the market as see above. 

The short window and long window are configured by a number of seconds, the data is then taken from the DB requesting `MACD_long_win_seconds`_ * 1.1. This is to get an extra 10% of data as there is usually some lost in the recording from Poloniex.
You can also use the `data_tolerance`_ to help with the amount of data required by the bot for this calculation, that is the number of seconds that can be missing for the data to still be valid.

This current implementation is basic in it's approach, but will be built upon with time. Results seem to be good though and we would welcome your feedback if you play around with it.

suggested loan rate
'''''''''''''''''''
If the average of the short window is greater than the average of the long window we will return the current

configuring
'''''''''''

The number of config options and combinations for this can be quite daunting. As time goes on I hope more people will feed back useful figures for all our different configuration set ups. I have put in sensible defaults into the config for the MACD section. These are options that I have changed that aren't set by default and work better if you're using MACD as the rate calculation method. Change the currency to whatever you want, though best not use more than 3 really, as it slows down the calls to poloniex considerably. If you can use just one, then do it.

I'm hoping that once more people test and report back results, this can be updated and more information passed to everyone else. 

The most important is probably the hidecoins change to False. This means that it will always place loans so you don't need to have as low a resolution on the sleep timers. You also want to make sure the gaptop and gapbottom are high so you can get a large spread.

======================= =========
Config                  Value
======================= =========
sleeptimeactive         10
sleeptimeinactive       10
spreadlend              3
gapMode                 RawBTC
gapbottom               40
gaptop                  200
hideCoins               False
analyseCurrencies       ETH,BTC
======================= =========

notes
'''''
- MACD will default back to the percentile method if it can't function. This will happen at start up for a while when it's collecting data and can also happen if something goes wrong with the Database or other failures. It's basically a failsafe to make sure you're still using some sort of market analsis while MACD is offline.
- You can turn on `ma_debug_log`_ to get some more information if things aren't working. 
- When it's start up you will see ``Need more data for analysis, still collecting. I have Y/X records``, so long as it's still increasing then this is fine. If it always prints that message then you should change your `data_tolerance`_



Recording currencies
````````````````````

All the options in this section deal with how data from poloniex is collected and stored. All the data is stored in an sqlite database, one per currency that you are recording. You can see the database files in the market_data folder of the bot.
There are a number of things to consider before configuring this section. The most important being that you can only make 6 api calls to poloniex every second. This limit includes returning your open loans, placing an loan and returning data for the live market to store in the database.

.. warning:: If you start to see the error message: ``HTTP Error 429: Too Many Requests`` then you need to review the settings in this file. In theory this shouldn't be a problem as our API limits calls to 6 per second. But it appears that it's not completely thread safe, so it can sometimes make more than 6 per second.
  If this happens, stop the bot. Increase your timer or decrease the number of recorded currencies, wait a five minutes, then start the bot again. Repeat as required.

analyseCurrencies
'''''''''''''''''

``analyseCurrencies`` is the list of currencies to record (and analyse)

None of the points below need be considered problematic unless you are planning to run with low (single digit seconds) timers on the bot. That is, the ``sleeptimeinactive``, ``sleeptimeactive`` and the ``analyseUpdateInterval``.

With that said, every currency you add to this will:

- Increase the number of db files (and therefore disk usage)
- Increase I/O and CPU usage (each currency will be writing to disk and if there's a balance, calculating the best rate)
- Reduce the number of requests you can make the API per second. This means times between stored records in the DB will be further apart and calls to place loans to Poloniex will be slower. 

configuration
~~~~~~~~~~~~~
==========  ===========================================================================================================
Format      ``CURRENCY_TICKER,STR,BTC,BTS,CLAM,DOGE,DASH,LTC,MAID,XMR,XRP,ETH,FCT,ALL,ACTIVE``
Disabling   Commenting it out will disable the entire feature.
``ACTIVE``  Entering ``ACTIVE`` analyses any currencies found in your lending account along with any other configured currencies.
``ALL``     Will analyse all coins on the lending market, whether or not you are using them.
Example     ``ACTIVE, BTC, CLAM`` will record and analyse BTC, CLAM, and any coins you are already lending.
Notes       Don't worry about duplicates when using ``ACTIVE``, they are handled internally.
==========  ===========================================================================================================

keep_history_seconds
''''''''''''''''''''
``keep_history_seconds`` is the maximum duration to store market data. Any data that is older that this number of seconds will be deleted from the DB.
This delete runs periodically, so it is possible for the there to be data older than the specified age in the database, however it won't be there for long.

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  86400 (1 day)
Allowed range  3600+
=============  ========================================================================================================

analyseUpdateInterval
'''''''''''''''''''''

``analyseUpdateInterval`` is how long the bot will sleep between requests for rate data from Poloniex. Each coin has it's own thread for requests and each thread has it's own sleep.
You are not guaranteed to get data at exactly the update interval. Setting it to 1 second, with several currencies
each one of them will take up one of the 6 API calls that are allowed per second. These calls need to be used to place
loans and other interactions with poloniex. 
Also, it can take some time to get data back from poloniex, because there is a single thread making all the requests
per currency, it will block the next request. I did have a multi threaded model for this currency recording, but it
frequently created too many threads when polo was lagging, causing more harm than good.

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  10
Allowed range  1 - 3600 (1 hour)
=============  ========================================================================================================


recorded_levels
'''''''''''''''

``recorded_levels`` is the number of rates found in the current offers on poloniex that will be recorded in the db. 
There is currently no reason to set this greater than 1 as we're not using the rest of the levels, this will change in the future though. You can raise it if you're examining the data yourself also. 

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  10
Allowed range  1 - 100
=============  ========================================================================================================



Analysing currencies
````````````````````
Everything in this section relates to how the analysis is carried out. So how much data is used and how it is used.

lendingStyle
''''''''''''

``lendingStyle`` lets you choose the percentile of each currency's market to lend at.

    - Recommendations: Conservative = 50, Moderate = 75, Aggressive = 90, Very Aggressive = 99
    - This is a percentile, so choosing 75 would mean that your minimum will be the value that the market is above 25% of the recorded time.
    - This will stop the bot from lending during a large dip in rate, but will still allow you to take advantage of any spikes in rate.

=============  ========================================================================================================
Default value  75
Allowed range  1-99
=============  ========================================================================================================


percentile_seconds
''''''''''''''''''

``percentile_seconds`` is the number of seconds worth of data to use for the percentile calculation. This value is not used in `MACD`_ methods.

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  86400
Allowed range  300 - ``keep_history_seconds``
=============  ========================================================================================================


MACD_long_win_seconds
'''''''''''''''''''''

``MACD_long_win_seconds`` is the number of seconds used for the long window average in the `MACD`_ method.

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  1800 (30 minutes)
Allowed range  300 - ``keep_history_seconds``
=============  ========================================================================================================


MACD_short_win_seconds
''''''''''''''''''''''

``MACD_short_win_seconds`` is the number of seconds used for the short window average in the `MACD`_ method.

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  150 (2.5 minutes)
Allowed range  25 - ``MACD_long_win_seconds``
=============  ========================================================================================================


data_tolerance
''''''''''''''

``data_tolerance`` is the percentage of data that can be missed from poloniex and still considered that we have enough data to work with. 
This was added because there are frequently problems with poloniex sending back data, also it's not always possible to get all the data you want if you are using multiple currencies. We are limited to 6 calls to poloniex every second.

If you keep seeing messages saying ``Need more data for analysis, still collecting. I have Y/X records``, then you
need to reduce this or reduce the number of currencies you are analysing.

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  15
Allowed range  10 - 90
=============  ========================================================================================================


daily_min_method
''''''''''''''''

``daily_min_method`` is the method in which you wish to calculate the daily_min for each currency. This is how we stop lending when the market rates are below average.
This can be either MACD or percentile. See `MACD`_ and `Percentile`_ sections for more information.
This will not change the `mindailyrate` that you have set for coins in the main config. So you will still never lend below what you have statically configured.

configuration
~~~~~~~~~~~~~
============== ========================================================================================================
Default value  MACD
Allowed values MACD, percentile
============== ========================================================================================================



MACD_multiplier
'''''''''''''''

``MACD_multiplier`` is what to scale up the returned average from the MACD calculation by. See `MACD`_ for more details.
In the future this will probably be removed in favour of sending back spread information that can be used for gaptop and gapbottom.

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  1.05
Allowed range  1 - 2
=============  ========================================================================================================


ma_debug_log
''''''''''''

``ma_debug_log`` when enabled will print to screen some of the internal information around the MACD and percentile calculations

configuration
~~~~~~~~~~~~~
=============  ========================================================================================================
Default value  False
Allowed range  True, False
=============  ========================================================================================================
