.. _configuration-section:

Configuration
*************

Configuring the bot can be as simple as copy-pasting your API key and Secret.

New features are required to be backwards compatible with previous versions of the .cfg but it is still recommended that you update your config immediately after updating to take advantage of new features.

To begin, copy ``default.cfg.example`` to ``default.cfg``. Now you can edit your settings.

API key and Secret
------------------

Create a **NEW** API key and Secret from `Poloniex <https://poloniex.com/apiKeys>`_ and paste them into the respective slots in the config.

    ``apikey = XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX``

    ``secret = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...``

Your API key is all capital letters and numbers in groups of 8, separated by hyphens.
Your secret is 128 lowercase letters and numbers.

HIGHLY Recommended:

    - Disable the "Enable Trading" checkbox. The bot does not need it to operate normally.
    - Enable IP filter to only the IP address the bot will be running from.

.. warning:: Do not share your API key nor secret with anyone whom you do not trust with all your Poloniex funds.

.. note:: If you use an API key that has been used by any other application, it will likely fail for one application or the other. This is because the API requires a `nonce <https://en.wikipedia.org/wiki/Cryptographic_nonce>`_.


Sleeptime
---------

- ``sleeptimeactive`` is how long the bot will "rest" (in seconds) between running while the bot has loan offers waiting to be filled.

    - Default value: 60 seconds
    - Allowed range: 1 to 3600 seconds
    - If the bot finishes a cycle and has no open lend orders left to manage, it will change to inactive mode.

.. note:: Just because 1 second is a permitted sleeptime does not mean it is a good idea.

- ``sleeptimeinactive`` is how long the bot will "rest" (in seconds) between running while the bot has nothing to do.

    - Default value: 300 seconds (5 minutes)
    - Allowed range: 1 to 3600 seconds
    - If the bot finishes a cycle and has lend orders to manage, it will change to active mode.

Min and Max Rates
-----------------

- ``mindailyrate`` is the minimum rate (in percent) that the bot will allow offer loans at.

    - Default value: 0.005 percent
    - Allowed range: 0.0031 to 5 percent
    - 0.0031% every day for a year, works out around 1%. This is less than most bank accounts and is considered not worth while.
    - The current default value is a optimistic but very viable for the more high volume currencies. Not viable for lending DOGE, for example.

- ``maxdailyrate`` is the maximum rate (in percent) that the bot will allow lends to open.

    - Default value: 5 percent
    - Allowed range: 0.0031 to 5 percent
    - 2% is the default value offered by the exchange, but there is little reason not to set it higher if you feel optimistic.

Spreading your Lends
--------------------

If ``spreadlend = 1`` and ``gapbottom = 0``, it will behave as simple lending bot lending at lowest possible offer.

- ``spreadlend`` is the amount (as an integer) of separate loans the bot will split your balance into across the order book.

    - Default value: 3
    - Allowed range: 1 to 20 (1 is the same as disabling)
    - The loans are distributed evenly between gapbottom and gaptop.
    - This allows the bot to benefit from spikes in lending rate but can result in loan fragmentation (not really a bad thing since the bot has to deal with it.)

- ``gapbottom`` is how far into the lending book (in percent of YOUR total balance for the respective coin) the bot will go, to start spreading loans.

    - Default value: 10 percent
    - Allowed range: 0 to <arbitrary large number> percent
    - 10% gapbottom is recommended to skip past dust at the bottom of the lending book, but if you have a VERY high volume this will cause issues as you stray to far away from the most competitive bid.

- ``gaptop`` is how far into the lending book (in percent of YOUR balance for the respective coin) the bot will go to stop spreading loans.

    - Default value: 200 percent
    - Allowed range: 0 to <arbitrary large number> percent
    - This value should be adjusted based on your coin volume to avoid going astronomically far away from a realistic rate.

Variable loan Length
--------------------

These values allow you to lock in a better rate for a longer period of time, as per your configuration.

- ``xdaythreshold`` is the rate (in percent) where the bot will begin attempting to lend for a longer period of time.

    - Default value: 0.2 percent
    - Allowed range: 0 to 5 percent

- ``xdays`` is the length(in days) of any loan whose rate exceeds the set xdaythreshold.

    - Default value: 60 days
    - Allowed range: 2 to 60 days

Auto-transfer from Exchange Balance
-----------------------------------

If you regularly transfer funds into your Poloniex account but don't enjoy having to log in yourself and transfer them to the lending balance, this feature is for you.

- ``transferableCurrencies`` is a list of currencies you would like to be transferred.

    - Default value: Commented out
    - Format: ``CURRENCY_TICKER,STR,BTC,BTS,CLAM,DOGE,DASH,LTC,MAID,XMR,XRP,ETH,FCT,ALL,ACTIVE``
    - Commenting it out will disable the feature.
    - Entering ``ACTIVE`` within the list will transfer any currencies that are found in your lending account, as well as any other currencies alongside it. Example: ``ACTIVE, BTC, CLAM`` will do BTC, CLAM, and any coins you are already lending.
    - Entering ``ALL`` will simply transfer all coins available to lending.
    - Do not worry about duplicates when using ``ACTIVE``, they are handled.
    - Coins will be transferred every time the bot runs (60 seconds by default) so if you intend to trade or withdrawal it is recommended to turn off the bot or disable this feature.

Unimportant settings
--------------------

Very few situations require you to change these settings.

- ``minloansize`` is the minimum size that a bot will make a loan at.

    - Default value: 0.01 of a coin
    - Allowed range: 0.01 and up.
    - If you dislike loan fragmentation, then this will make the minimum for each loan larger.
    - Automatically adjusts to at least meet the minimum of each coin.

- ``KeepStuckOrders`` If True, keeps orders that are "stuck" in the market instead of canceling them.

    - Default value: True
    - Allowed values: True or False
    - A "Stuck" order occurs when it partially fills and leaves the coins balance total (total = open orders + let in balance) below your ``minloansize`` and so the bot would not be able to lend it again if it was canceled.
    - When disabled, stuck orders will be canceled and held in balance until enough orders expire to allow it to lend again.

- ``hideCoins`` If True, will not lend any of a coin if its market low is below the set ``mindailyrate``.

    - Default value: True
    - Allowed values: True or False. Commented defaults to True
    - This hides your coins from appearing in walls.
    - Allows you to catch a higher rate if it spikes past your ``mindailyrate``.
    - Not necessarily recommended if used with ``analyseCurrencies`` with an aggressive ``lendingStyle``, as the bot may miss short-lived rate spikes.
    - If you are using the ``analyseCurrencies`` option, you will likely see a lot of ``Not lending BTC due to rate below 0.9631%`` type messages in the logs. This is normal.

- ``endDate`` Bot will try to make sure all your loans are done by this date so you can withdraw or do whatever you need.

    - Default value: Disabled
    - Uncomment to enable.
    - Format: ``YEAR,MONTH,DAY``

Max to be lent
--------------

This feature group allows you to only lend a certain percentage of your total holding in a coin, until the lending rate suprasses a certain threshhold. Then it will lend at max capacity.

- ``maxtolend`` is a raw number of how much you will lend of each coin whose lending rate is below ``maxtolendrate``.

    - Default value: Disabled
    - Allowed range: 0 (disabled) or ``minloansize`` and up
    - If set to 0, same as if commented.
    - If disabled, will check if ``maxpercenttolend`` is enabled and use that if it is enabled.
    - Setting this overwrites ``maxpercenttolend``
    - This is a global setting for the raw value of coin that will be lent if the coins lending value is under ``maxtolendrate``
    - Has no effect if current rate is higher than ``maxtolendrate``
    - If the remainder (after subtracting ``maxtolend``) in a coin's balance is less than ``minloansize``, then the remainder will be lent anyway. Otherwise, the coins would go to waste since you can't lend under ``minloansize``

- ``maxpercenttolend`` is a percentage of how much you will lend of each coin whose lending rate is below ``maxtolendrate``

    - Default value: Disabled
    - Allowed range: 0 (disabled) to 100 percent
    - If set to 0, same as if commented.
    - If disabled in addition to ``maxtolend``, entire feature will be disabled.
    - This percentage is calculated per-coin, and is the percentage of the balance that will be lent if the coin's current rate is less than ``maxtolendrate``
    - Has no effect if current rate is higher than ``maxtolendrate``
    - If the remainder (after subtracting ``maxpercenttolend``'s value) in a coin's balance is less than ``minloansize``, then the remainder will be lent anyway. Otherwise, the coins would go to waste since you can't lend under ``minloansize``


- ``maxtolendrate`` is the rate threshold when all coins are lent.

    - Default value: Disabled
    - Allowed range: 0 (disabled) or ``mindailyrate`` to 5 percent
    - Setting this to 0 with a limit in place causes the limit to always be active.
    - When an indiviaual coin's lending rate passes this threshold, all of the coin will be lent instead of the limits ``maxtolend`` or ``maxpercenttolend``


Market Analysis
---------------

This feature allows you to record a currency's market and have the bot see trends. With this data, we can compute a recommended minimum lending rate per currency to avoid lending at times when the rate dips.

- ``analyseCurrencies`` is the list of currencies to analyse.

    - Format: ``CURRENCY_TICKER,STR,BTC,BTS,CLAM,DOGE,DASH,LTC,MAID,XMR,XRP,ETH,FCT,ALL,ACTIVE``
    - Commenting it out will disable the entire feature.
    - Entering ``ACTIVE`` within the list will analyse any currencies that are found in your lending account, as well as any other currencies alongside it. Example: ``ACTIVE, BTC, CLAM`` will do BTC, CLAM, and any coins you are already lending.
    - Entering ``ALL`` will simply analyse all coins on the lending market, whether or not you are using them.
    - Do not worry about duplicates when using ``ACTIVE``, they are handled.


- ``analyseMaxAge`` is the maximum duration to store market data.

    - Default value: 30 days
    - Allowed range: 1-365 days

- ``analyseUpdateInterval`` is how often (asynchronous to the bot) to record each market's data.

     - Default value: 60 seconds
     - Allowed range: 10-3600 seconds

 .. note:: Storage usage caused by the above two settings can be calculated by: ``<amountOfCurrencies> * 30 * analyseMaxAge * (86,400 / analyseUpdateInterval)`` bytes. Default settings with ``ALL`` currencies enabled will result in using ``15.552 MegaBytes`` maximum.

- ``lendingStyle`` lets you choose the percentile of each currency's market to lend at.

    - Default value: 75
    - Allowed range: 1-99
    - Recommendations: Conservative = 50, Moderate = 75, Aggressive = 90, Very Aggressive = 99
    - This is a percentile, so choosing 75 would mean that your minimum will be the value that the market is above 25% of the recorded time.
    - This will stop the bot from lending during a large dip in rate, but will still allow you to take advantage of any spikes in rate.


Config per Coin
---------------

This can be configured in one of two ways. 

**Coincfg dictionary**

- ``coincfg`` is in the form of a dictionary and allows for advanced, per-coin options.

    - Default value: Commented out, uncomment to enable.
    - Format: ``["COINTICKER:MINLENDRATE:ENABLED?:MAXTOLEND:MAXPERCENTTOLEND:MAXTOLENDRATE","CLAM:0.6:1:0:.75:.1",...]``
    - COINTICKER refers to the ticker of the coin, ex. BTC, CLAM, MAID, DOGE.
    - MINLENDRATE is that coins minimum lending rate, overrides the global setting. Follows the limits of ``minlendrate``
    - ENABLED? refers to a value of ``0`` if the coin is disabled and will no longer lend. Any positive integer will enable lending for the coin.
    - MAXTOLEND, MAXPERCENTTOLEND, and MAXTOLENDRATE refer to their respective settings above, but are unique to the specified coin specifically.
    - There can be as many different coins as you want in coincfg, but each coin may only appear once.

**Separate coin sections**

This is an alternative layout for the coin config mentioned above. It provides the ability to change the minloansize per coin, but is otherwise identical in functionality.
To use this configuration, make sure to comment out the line where coincfg is defined, then add a section for each coin you wish to configure.

.. warning:: These sections should come at the end of the file, after the other options for the bot.

Configuration should look like this::

    [BTC]
    minloansize = 0.01
    mindailyrate = 0.1
    maxactiveamount = 1
    maxtolend = 0
    maxpercenttolend = 0
    maxtolendrate = 0


Advanced logging and Web Display
--------------------------------

- ``jsonfile`` is the location where the bot will log to a .json file instead of into console.

    - Default value: Commented out, uncomment to enable.
    - Format: ``www/botlog.json``
    - This is the location relative to the running instance of the bot where it will store the .json file. The default location is recommended if using the webserver functionality.

- ``jsonlogsize`` is the amount of lines the botlog will keep before deleting the oldest event.

    - Default value: Commented out, uncomment to enable.
    - Format: ``200``
    - Reasons to lower this include: you are conscious of bandwidth when hosting your webserver, you prefer (slightly) faster loading times and less RAM usage of bot.

- ``startWebServer`` if true, this enables a webserver on the www/ folder.

    - Default value: Commented out, uncomment to enable.
    - The server page can be accessed locally, at ``http://localhost:8000/lendingbot.html`` by default.
    - You must close bot with a keyboard interrupt (CTRL-C on Windows) to properly shutdown the server and release the socket, otherwise you may have to wait several minutes for it to release itself.

- ``customWebServerAddress`` is the IP address and port that the webserver can be found at.

    - Advanced users only.
    - Default value: 0.0.0.0:8000 Uncomment to change
    - Format: ``IP:PORT``
    - Setting the ip to ``127.0.0.1`` will ONLY allow the webpage to be accessed at localhost (``127.0.0.1``)
    - Setting the ip to ``0.0.0.0`` will allow the webpage to be accessed at localhost (``127.0.0.1``) as well as at the computer's LAN IP address within the local network. This option is the most versatile, and is default.
    - Setting the ip to ``192.168.0.<LAN IP>`` will ONLY allow the webpage to be access at the computer's LAN IP address within the local network (And not through localhost.) It is recommended to be sure the device has a static local IP.
    - Do not set the port to a `reserved port <http://www.ingate.com/files/422/fwmanual-en/xa10285.html>`_ or you will receive an error when running the bot or attempting to connect (depending on HOW reserved a port is.)
    - You must know what you are doing when changing the IP address to anything other than the three suggested configurations above.

- ``outputCurrency`` this is the ticker of the coin which you would like the website to report your summary earnings in.

    - Default value: BTC
    - Acceptable values: BTC, USDT, Any coin with a direct Poloniex BTC trading pair (ex. DOGE, MAID, ETH), Currencies that have a BTC exchange rate on blockchain.info (i.e. EUR, USD)
    - Will be a close estimate, due to unexpected market fluctuations, trade fees, and other unforseeable factors.

Plugins
-------

Plugins allow extending Bot functionality with extra features.
To enable/disable a plugin add/remove it to the ``plugins`` list config option, example::

    plugins = Plugin1, Plugin2, etc...

AccountStats Plugin
~~~~~~~~~~~~~~~~~~~

The AccountStats plugin fetches all your loan history and provides statistics based on it.
Current implementation sends a earnings summary Notification (see Notifications sections) every 24hr.

To enable the plugin add ``AccountStats`` to the ``plugins`` config options, example::

    plugins = AccountStats

Be aware that first initialization might take longer as the bot will fetch all the history.

lendingbot.html options
-----------------------

You can pass options to statistics page by adding them to URL. Eg, ``http://localhost:8000/lendingbot.html?option1=value&option2=0``

- ``effrate`` controls how effective loan rate is calculated. Yearly rates are calculated based on effective rate, so this option affects them as well. Last used mode remembered by browser, so you do not have to specify this option every time. By default, effective loan rate is calculated considering lent precentage (from total available coins) and poloniex 15% fee.

    - Allowed values: ``lentperc``, ``onlyfee``.
    - Default value: ``lentperc``.
    - ``onlyfee`` calculates effective rate without considering lent coin percentage.

- ``displayUnit`` controls BTC's unit output.

    - Allowed values: ``BTC``, ``mBTC``, ``Bits``, ``Satoshi``
    - Default value: ``BTC``
    - This setting will change all display of Bitcoin to that unit. Ex. 1 BTC -> 1000 mBTC.

- ``earningsInOutputCurrency`` define which earnings are shown in the output currency.

    - Allowed values: ``all``, ``summary``
    - Default value: ``all``


Notifications
-------------
The bot supports sending notifications for serveral different events on several different platforms. To enable notifications, you must first have a section in your config called ``[notifications]``, inside which you should enable at least one of the following events and also at least one notification platfom. The list of events you can notify about are:

Notification events
~~~~~~~~~~~~~~~~~~~

- ``notify_new_loans``

    - Sends a notification each time a loan offer is filled.

- ``notify_tx_coins``

    - This will send a notification if any coins are transferred from your exchange account, to your lending account. You must have ``transferableCurrencies`` enabled for this to work.  Then you should set ``notify_tx_coins = True``.

- ``notify_xday_threshold``

    - This will send a notification every time a loan is created that is above your ``xdaythreshold`` config value. To enable you should set ``notify_xday_threshold = True``.

- ``notify_summary_minutes``

    - This will send a summary of the current loans you have every X minutes. This is similar to the information you get in the log line when running the bot, or the line a the top of the web page. To enable this add ``notify_summary_minutes = 120``. This will send you a notification every 2 hours (120 minutes).

- ``notify_caught_exception``

    - This is more useful for developers and people wanting to help out by raising issues on github. This will send a notification every time there is an exception thrown in the bot that we don't handle. To enable add ``notify_caught_exception = True``.

Once you have decided which notifications you want to recive, you can then go about configuring platforms to send them on. Currently the bot supports:

Email notifications
~~~~~~~~~~~~~~~~~~~

This is probably the easiest to configure, though there can still be issues with gmail where you need to enable a few things. You can find out more about that `here <https://support.google.com/mail/answer/7126229?visit_id=1-636225201534132377-750209621&rd=2#cantsignin>`_ if you're having problems. If you don't wish to use gmail search google for the smtp settings of your email provider.
To enable email you should configure the following::

    email = True
    email_login_address = me@gmail.com
    email_login_password = secretPassword
    email_smtp_server = smtp.gmail.com
    email_smtp_port = 465
    email_smtp_starttls = False
    email_to_addresses = me@gmail.com,you@gmail.com

Slack notifications
~~~~~~~~~~~~~~~~~~~

Before you can post to slack you need to create an API token, to do this visit `this page <https://api.slack.com/docs/oauth-test-tokens>`_. Once you have a token you can then configure the bot as so::

    slack = True
    slack_token = xoxp-46351793751-46348393136-47931965411-a8757952e4
    slack_channels = #cryptocurrency,@someUser

To post in a channel prefix with # and to post a dm to a user prefix with @. You can send to as many channels or users as you want.

Telegram notifications
~~~~~~~~~~~~~~~~~~~~~~

Quickstart
  To have telegram notifications you need to get a bot id from the BotFather. You can do that `here <https://core.telegram.org/bots>`_.
  Once you have a bot id you need to get your Chat ID or create a channel and invite the bot so it can chat there. Once you have all this in place you configure it like so::

    telegram = True
    telegram_bot_id = 281421543:AGGB1TqP7XqhxhT7VOty0Aml8DV_R6kimHw
    telegram_chat_ids = 123456789,@cryptocurrency

Detailed
  Messages are sent to the telegram bot API using HTTPS requests. You can read more about it `here <https://core.telegram.org/bots/api>`_.

  Telegram Bots are special accounts that do not require an additional phone number to set up, they do however need a unique authentication token. This is the token we need to get and add to the lendingbot's default.cfg. They are normally in the format ``123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11``.
  
  When we say we are creating a new telegram bot, all it means is that we are creating an account for the lendingbot to send message through. To create a bot and get a token, we must request it from the BotFather. This is telegram's tool for creating new bots. 
  
  These are the steps to carry out:
    1. Install the telegram desktop client from `their site <https://telegram.org/apps>`_. Then set it up with your phone number and login.
    2. Start a conversation with `The BotFather <https://telegram.me/botfather>`_. When you click the link it should open up in the telegram desktop client.
    3. Once you have a conversation started type ``/newbot``, you'll then be asked what to call the bot and it's username. The name of your bot is displayed in contact details and elsewhere. The Username is a short name, to be used in mentions and telegram.me links. When complete you'll receive a token.
    4. You can check everything is working OK by going to https://api.telegram.org/bot*YOURTOKEN*/getme, for example my test one is https://api.telegram.org/bot288427377:AAGB1TqL7XqhxhT7VOxu8Ams8DV_J6kimHw/getme. If that's all working then move on to the next step.
    5. Now we need somewhere to send the messages, if you want to send a message to yourself, you first need your Chat ID. The easiest way I've found to get this is to send the bot a message from your desktop client and then use the getupdates method. So search for the bot in the desktop client's search bar and start a conversation. Then in your browser go to https://api.telegram.org/bot*YOURTOKEN*/getupdates. You should see a few lines of text, the one we're interested in looks like ``"chat":{"id":123456789,"first_name":"Michael","last_name":"Robinson","type":"private"}``. The number after ID is your chat ID.
    6. Again, just to check everything is working, lets send ourselves a message. You can do this by putting this in your browser https://api.telegram.org/bot*YOURTOKEN*/sendmessage?text=TEST%20BOT&chat_id=*YOUR_CHAT_ID* You should see a message in your desktop client. If so you have the right ID and we can move on.
    7. The last step to get it working is just adding the two values to your default.cfg file and turning on ``telegram = True``. You should set ``telegram_bot_id`` to the token you got from the BotFather, and set the ``telegram_chat_ids`` to a comma separated list of people you want to send messages to.
    8. (optional) If you'd like a specific channel for the bot to send messages you can follow these steps.
        a. Open the desktop client and create a new channel
        b. Start a conversation with the BotFather and type /setjoingroups, then follow the questsions he asks.
        c. Click on the message we sent earlier from the bot, then click on the bot's name in the conversation. You should see 'Add To Group'. Click this and add it to the new group you created.
        d. Now you should be able to add the ``@nameOfChannel`` to your ``default.cfg`` file and post all the updates there too. Make sure the list is comma separated and you have the '@' infront of the channel name. This is only done for names, not Chat IDs.

Pushbullet notifications
~~~~~~~~~~~~~~~~~~~~~~~~

To enable `Pushbullet <https://www.pushbullet.com/>`_ notifications, you first need to create an API key and then discover your device ID.

Visit your `Account Settings <https://www.pushbullet.com/#settings/account>`_ and click 'Create Access Token'. Add this to the config file as shown below.

You then need to visit this `documentation page <https://docs.pushbullet.com/#list-devices>`_ and run the example curl command for listing your devices (be sure to substitute your API token as created in the previous step). Copy the value listed for 'iden' into the config file as shown below.::

    pushbullet = True
    pushbullet_token = l.2mDDvy4RRdzcQN9LEWSy22amS7u3LJZ1
    pushbullet_deviceid = ujpah72o0sjAoRtnM0jb
