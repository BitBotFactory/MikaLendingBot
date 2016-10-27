3. Contributing
***************

3.1 How to format Python Code
=============================

3.1.1 PEP8
----------

Poloniex lending bot follows `PEP8 styling guidelines <https://www.python.org/dev/peps/pep-0008/>`_ to maximize code readibility and maintenance.

To help out users and automate much of the process, `the Hound Continuous Integration bot <https://houndci.com/configuration#python>`_ will comment on pull requests to alert you to any changes you need to make.
Hound follows ``flake8`` standards, which may extend past PEP8 conventions. We recommend you follow its suggestions as much as possible. 

To make following PEP8 as painless as possible, we strongly recommend using an Integrated Development Environment that features PEP8 suggestions, such as `PyCharm <https://www.jetbrains.com/pycharm/>`_.

3.1.2 Indent Style
---------------------

You may have your own preference, it does not matter because *spaces and tabs do not mix.*

Poloniexlendingbot uses *tabs.*

Tabs can be configured in your IDE to be as long or as short as you wish, the same can not be done with spaces. Case closed.

3.1.3 Commenting Code
---------------------

Many coders learned to code without commenting their logic.
That works if you are the only person working on the project, but quickly becomes a problem when it is your job to decipher what someone else was thinking when coding.

Please comment your code, at least every couple lines to assist in following along with the code logic. Especially if you are using some sort of esoteric hack.

3.1.4 Variable or Option Naming
-------------------------------

Whenever you create a variable or configuration option, we recommend using `camelCase <https://en.wikipedia.org/wiki/Camel_case>`_ with the first letter uncapitalized.

Do not make global single-letter variable names, those do not help anybody. Using them within a function for a few lines in context is okay, but calling it much later should require it be given a proper name.
