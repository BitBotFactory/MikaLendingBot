Contributing
************

How to format Python Code
=========================

If you want to make a successful pull request, `here are some suggestions. <http://blog.ploeh.dk/2015/01/15/10-tips-for-better-pull-requests/>`_

Recommended IDE: `PyCharm <https://www.jetbrains.com/pycharm/>`_

PEP8
----

Poloniex lending bot follows `PEP8 styling guidelines <https://www.python.org/dev/peps/pep-0008/>`_ to maximize code readability and maintenance.

To help out users and automate much of the process, `the Codacy Continuous Integration bot <https://www.codacy.com/app/PoloniexLendingBot/poloniexlendingbot/dashboard>`_ will comment on pull requests to alert you to any changes you need to make.
Codacy has many inspections it does, which may extend past PEP8 conventions. We recommend you follow its suggestions as much as possible.

To make following PEP8 as painless as possible, we strongly recommend using an Integrated Development Environment that features PEP8 suggestions, such as `PyCharm <https://www.jetbrains.com/pycharm/>`_.

Indent Style
------------

You may have your own preference, it does not matter because *spaces and tabs do not mix.*

Poloniexlendingbot uses *spaces* to conform with PEP8 standards. Please use an IDE that can help you with this.

Commenting Code
---------------

Many coders learned to code without commenting their logic.
That works if you are the only person working on the project, but quickly becomes a problem when it is your job to decipher what someone else was thinking when coding.

You will probably be relieved to read that code comments are not mandatory, because `code comments are an apology. <http://butunclebob.com/ArticleS.TimOttinger.ApologizeIncode>`_

Only comment your code if you need to leave a note. (We won't judge you for it.)

Variable or Option Naming
-------------------------

Whenever you create a variable or configuration option, follow PEP8 standards, they are as follows:

    Do not make global single-letter variable names, those do not help anybody. Using them within a function for a few lines in context is okay, but calling it much later requires it be given a proper name.

    Functions are named like ``create_new_offer()`` and variables are named similarly, like ``amount_of_lends``.

Line Length
-----------

To make it simple to review code in a diff viewer (and several other reasons) line length is limited to 128 characters in Python code.

Python allows plenty of features for one line to be split into multiple lines, those are permitted.

Configuration Options
---------------------

New configuration options should be placed near similar options (see categories on the configuration page) and require a short description above the actual setting.

If a setting is added that changes functionality, it is required that you add handling for having the option commented out.

How to use the Configuration module:

    - If your change is in a new module, you need to init it to import the Config object. Create a function init(<args>) that set the args to global variables within the module. With this, pass Config from the main of the bot.
    - Use ``option = Config.get(CATEGORY, OPTION, DEFAULT_VALUE, LOWER_LIMIT, UPPER_LIMIT)`` to get the option from the Config. Only do this in your init()
    - CATEGORY: The category of the config file it goes under. Currently there is only 'API' and 'BOT'
    - OPTION: Case-sensitive name of the option you are pulling from the bot.
    - DEFAULT_VALUE: Default: False. This is the value that .get() will return if no value is set (option is commented). If set to "None": the bot will not allow it to be left blank ever. Optional.
    - LOWER_LIMIT: Default: False. The lower float value that the option can be set to. If OPTION's value is lesser than this, the bot will alert them and exit. Optional. Only use for numerical options.
    - UPPER_LIMIT: Default: False. The upper float value that the option can be set to. If OPTION's value is greater than this, the bot will alert them and exit. Optional. Only use for numerical options.

``Config.has_option(CATEGORY, OPTION)`` will always return a boolean for whether the option exists or not. If the option is commented it will return False.


Making Documentation
====================

It is important to keep proper documentation of configuration options, to make it as clear as possible for the user.

Building Docs
-------------

If you want to be able to build the html files of the documentation, you need to have Sphinx installed. You can install this with ``pip install sphinx``.
From there, run ``make html`` in the docs directory. These instructions can also be found in the included README.

Writing Docs
------------

Just follow the lead of the rest of the docs.

- Configurations need a default, allowed values, effect, etc. in a format similar to the other options.
- Installation instructions should be similar to a followable list.


Javascript
==========

Codacy will offer suggestions for fixes to standardize/fix the code. Do not worry about having too many commits in your PR.

Lendingbot.js is already quite messy, so following Codacy's suggestions is highly encouraged.
