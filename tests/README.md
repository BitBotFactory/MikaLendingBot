#Poloniex lending bot tests

All tests are written to work with pytest, they also use hypothesis. These are both available through PyPi using pip

`pip install hypothesis pytest`

For all the tests to work correctly you will also need numpy installed

`pip install numpy`

Currently there are only tests for the MarketAnalysis module though more will be added as time goes on. 

To run the tests, you need to have a config file that has a correct key to talk to Poloniex, it won't make any trades or do anything to your account, it's a problem with how we initialise modules at the minute.
Then, cd to the root of the source code and run:

`pytest tests/`

That's it! If you come across any problems, make sure it's not something in your code. If you're sure it's an issue then please raise it on github.
