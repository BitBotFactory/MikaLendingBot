.. _configuration-section:

2. Configuration
*****************

Configuring the bot can be as simple as copy-pasting your API key and Secret.

New features are required to be backwards compatible with previous versions of the .cfg but it is still recommended that you update your config immediately after updating to take advantage of new features.

To begin, copy ``default.cfg.example`` to ``default.cfg``. Now you can edit your settings.

2.1 API key and Secret
---------------------------

CREATE A NEW API key and Secret from `Poloniex <https://poloniex.com/apiKeys>`_ and paste them into the respective slots in the config. 

	apikey = XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
	
	secret = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Your API key is all capital letters and numbers in groups of 8, separated by hyphens.
Your secret is 128 lowercase letters and numbers.

HIGHLY Recommended:

- Disable the "Enable Trading" checkbox. The bot does not need it to operate normally.
- Enable IP filter to only the IP address the bot will be running from.

.. warning:: Do not share your API key nor secret with anyone whom you do not trust with all your Poloniex funds.

.. note:: If you use an API key that has been used by any other application, it will likely fail for one application or the other. This is because the API requires a `nonce <https://en.wikipedia.org/wiki/Cryptographic_nonce>`_.


2.2 Sleeptime
-----------------

``sleeptimeactive`` is how long the bot will "rest" (in seconds) between running while the bot has lends waiting to be filled.

- Default value: 60 seconds 
- Allowed range: 1 to 3600 seconds
- If the bot finishes a cycle and has no open lend orders left to manage, it will change to inactive mode.

.. note:: Just because 1 second is a permitted sleeptime does not mean it is a good idea.

``sleeptimeinactive`` is how long the bot will "rest" (in seconds) between running while the bot has nothing to do. 

- Default value: 300 seconds (5 minutes)
- Allowed range: 1 to 3600 seconds
- If the bot finishes a cycle and has lend orders to manage, it will change to active mode.

2.3 Min and Max Rates
---------------------------

``mindailyrate`` is the minimum rate (in percent) that the bot will allow lends to open.

- Default value: 0.04 percent
- Allowed range: 0.0031 to 5 percent
- It is not worth it to settle at a low rate, 0.0031% every day for a year comes out to about 1%. That is worse than bank interest.
- The current default value is a optimistic but very viable for the more high volume currencies. Not viable for lending DOGE, for example.

``maxdailyrate`` is the maximum rate (in percent) that the bot will allow lends to open.

- Default value: 2 percent
- Allowed range: 0.0031 to 5 percent 
- 2% is the default value offered by the exchange, but there is little reason not to set it higher if you feel optimistic.

2.4 Spreading your Lends
---------------------------

If `spreadlend = 1` and `gapbottom = 0`, it will behave as simple lending bot lending at lowest possible offer.

``spreadlend`` is the amount (as an integer) of separate lends the bot will split your balance into across the order book.

- Default value: 3
- Allowed range: 1 to 20 (1 is the same as disabling)
- The lends are distributed evenly between gapbottom and gaptop.
- This allows the bot to benefit from spikes in lending rate but can result in loan fragmentation (not really a bad thing since the bot has to deal with it.)

``gapbottom`` is how far into the lending book (in percent of YOUR balance for the respective coin) the bot will go to start spreading lends. 

- Default value: 10 percent
- Allowed range: 0 to <arbitrary large number> percent
- 10% gapbottom is recommended to skip past dust at the bottom of the lending book, but if you have a VERY high volume this will cause issues as you stray to far away from the most competitive bid.

``gaptop`` is how far into the lending book (in percent of YOUR balance for the respective coin) the bot will go to stop spreading lends. 

- Default value: 200
- Allowed range: 0 to <arbitrary large number> percent
- This value should be adjusted based on your coin volume to avoid going astronomically far away from a realistic rate.

2.5 Variable loan Length
---------------------------

These values allow you to lock in a better rate for a longer period of time, as per your configuration.

``xdaythreshold`` is the rate (in percent) where the bot will begin attempting to lend for a longer period of time.

- Default value: 0.2 percent
- Allowed range: 0 to 5 percent 

``xdays`` is the length(in days) of any loan whose rate exceeds the set xdaythreshold.

- Default value: 60 days
- Allowed range: 2 to 60 days

2.6 Unimportant settings
------------------------

Very few situations require you to change these settings.

``minloansize`` is the minimum size that a bot will make a loan at.

- Default value: 0.001 of a coin
- Allowed range: 0.001 and up.
- If you dislike loan fragmentation, then this will make the minimum for each loan larger.

``autorenew`` If 0, does nothing. If 1, will enable autorenew on loans once the bot closes with CTRL-C.

2.7 Max to be lent 
-------------------

This feature group allows you to only lend a certain percentage of your total holding in a coin, until the lending rate suprasses a certain threshhold. Then it will lend at max capacity.

``maxtolent`` is a raw number of how much you will lend of each coin whose lending rate is below ``maxtolentrate``.

- Default value: Disabled
- Allowed range: 0 (disabled) or ``minloansize`` and up
- If set to 0, same as if commented.
- If disabled, will check if ``maxpercenttolent`` is enabled and use that if it is enabled.
- Setting this overwrites ``maxpercenttolent``
- This is a global setting for the raw value of coin that will be lended if the coins lending value is under ``maxtolentrate``
- Has no effect if current rate is higher than ``maxtolentrate``
- If the remainder (after subtracting ``maxtolent``) in a coin's balance is less than ``minloansize``, then the remainder will be lent anyway. Otherwise, the coins would go to waste since you can't lend under ``minloansize``

``maxpercenttolent`` is a percentage of how much you will lend of each coin whose lending rate is below ``maxtolentrate``

- Default value: Disabled
- Allowed range: 0 (disabled) to 100 percent
- If set to 0, same as if commented.
- If disabled in addition to ``maxtolent``, entire feature will be disabled.
- This percentage is calculated per-coin, and is the percentage of the balance that will be lended if the coin's current rate is less than ``maxtolentrate``
- Has no effect if current rate is higher than ``maxtolentrate``
- If the remainder (after subtracting ``maxpercenttolent``'s value) in a coin's balance is less than ``minloansize``, then the remainder will be lent anyway. Otherwise, the coins would go to waste since you can't lend under ``minloansize``


``maxtolentrate`` is the rate threshold when all coins are lent.

- Default value: Disabled
- Allowed range: 0 (disabled) or ``mindailyrate`` to 5 percent
- Setting this to 0 with a limit in place causes the limit to always be active.
- When an indiviaual coin's lending rate passes this threshold, all of the coin will be lent instead of the limits ``maxtolent`` or ``maxpercenttolent``


2.8 Config per Coin
----------------------

``coincfg`` is in the form of a dictionary and allows for advanced, per-coin options.

- Default value: Commented out, uncomment to enable.
- Format: ``["COINTICKER:MINLENDRATE:ENABLED?:MAXTOLENT:MAXPERCENTTOLENT:MAXTOLENTRATE","CLAM:0.6:1:0:.75:.1",...]``
- COINTICKER refers to the ticker of the coin, ex. BTC, CLAM, MAID, DOGE.
- MINLENDRATE is that coins minimum lending rate, overrides the global setting. Follows the limits of ``minlendrate``
- ENABLED? refers to a value of ``0`` if the coin is disabled and will no longer lend. Any positive integer will enable lending for the coin.
- MAXTOLENT, MAXPERCENTTOLENT, and MAXTOLENTRATE refer to their respective settings above, but are unique to the specified coin specifically.
- There can be as many different coins as you want in coincfg, but each coin may only appear once.

2.9 Advanced logging and Web Display
--------------------------------------

``jsonfile`` is the location where the bot will log to a .json file instead of into console.

- Default value: Commented out, uncomment to enable.
- Format: ``www/botlog.json``
- This is the location relative to the running instance of the bot where it will store the .json file. The default location is recommended if using the webserver functionality.

``jsonlogsize`` is the amount of lines the botlog will keep before deleting the oldest event.

- Default value: Commented out, uncomment to enable.
- Format: ``200``
- Reasons to lower this include: you are conscious of bandwidth when hosting your webserver, you prefer (slightly) faster loading times and less RAM usage of bot.

``startwebserver`` if true, this enables a webserver on the www/ folder.

- Default value: Commented out, uncomment to enable.
- The server page can be accessed locally at ``http://127.0.0.1:8000/lendingbot.html``
- If you want to access this page remotely, you need to modify line 420 (as of 10/11/16) to change HOST to ``0.0.0.0``. You may then access the webpage on ``<computer local IP address>:8000/lendingbot.html``.
- You must close bot with a keyboard interrupt (CTRL-C on Windows) to properly shutdown the server and release the socket, otherwise you will have to wait several minutes for it to release itself.

``outputCurrency`` this is the ticker of the coin which you would like the website to report your summary earnings in.

- Default value: BTC
- Acceptable values: BTC, USDT, Any coin with a direct Poloniex BTC trading pair (ex. DOGE, MAID, ETH)
- Will be a close estimate, due to unexpected market fluctuations, trade fees, and other unforseeable factors.
