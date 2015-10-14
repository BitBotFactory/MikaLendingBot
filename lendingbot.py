import io, sys, time, datetime, urllib2, json
from poloniex import Poloniex
from ConfigParser import SafeConfigParser
from Logger import Logger
from decimal import *

SATOSHI = Decimal(10) ** -8

config = SafeConfigParser()
config_location = 'default.cfg'

defaultconfig =\
"""
[API]
apikey = YourAPIKey
secret = YourSecret

[BOT]
#sleep between iterations, time in seconds
sleeptime = 60
#minimum daily lend rate in percent
mindailyrate = 0.01
#max rate. 2% is good choice because it's default at margin trader interface. 5% is max to be accepted by the exchange
maxdailyrate = 2
#The number of offers to split the available balance uniformly across the [gaptop, gapbottom] range.
spreadlend = 3
#The depth of lendbook (in percent of lendable balance) to move through before placing the first (gapbottom) and last (gaptop) offer.
#if gapbottom is set to 0, the first offer will be at the lowest possible rate. However some low value is recommended (say 10%) to skip dust offers
gapbottom = 1
gaptop = 100
#Daily lend rate threshold after which we offer lends for 60 days as opposed to 2. If set to 0 all offers will be placed for a 2 day period
sixtydaythreshold = 0.2
#custom config per coin, useful when closing positions etc.
#syntax: [COIN:mindailyrate:maxactiveamount, ... COIN:mindailyrate:maxactiveamount]
#if maxactive amount is 0 - stop lending this coin. in the future you'll be able to limit amount to be lent.
#coinconfig = ["BTC:0.18:1","CLAM:0.6:1"]
"""

loadedFiles = config.read([config_location])
#Create default config file if not found
if len(loadedFiles) != 1:
	config.readfp(io.BytesIO(defaultconfig))
	with open(config_location, "w") as configfile:
		configfile.write(defaultconfig)
		print 'Edit default.cnf file with your api key and secret values'
		exit(0)


sleepTime = float(config.get("BOT","sleeptime"))
minDailyRate = Decimal(config.get("BOT","mindailyrate"))/100
maxDailyRate = Decimal(config.get("BOT","maxdailyrate"))/100
spreadLend = int(config.get("BOT","spreadlend"))
gapBottom = Decimal(config.get("BOT","gapbottom"))
gapTop = Decimal(config.get("BOT","gaptop"))
sixtyDayThreshold = float(config.get("BOT","sixtydaythreshold"))/100

try:
	coincfg = {} #parsed
	coinconfig = (json.loads(config.get("BOT","coinconfig")))
	#coinconfig parser
	for cur in coinconfig:
		cur = cur.split(':')
		coincfg[cur[0]] = dict(minrate=(Decimal(cur[1]))/100, maxactive=Decimal(cur[2]))
except Exception as e:
	pass
	
#sanity checks
if sleepTime < 1 or sleepTime > 3600:
	print "sleeptime value must be 1-3600"
	exit(1)
if minDailyRate < 0.00003 or minDailyRate > 0.05: # 0.003% daily is 1% yearly
	print "mindaily rate is set too low or too high, must be 0.003-5%"
	exit(1)
if maxDailyRate < 0.00003 or maxDailyRate > 0.05:
	print "maxdaily rate is set too low or too high, must be 0.003-5%"
	exit(1)
if spreadLend < 1 or spreadLend > 20:
	print "spreadlend value must be 1-20 range"
	exit(1)

dryRun = False
try:
	if sys.argv.index('--dryrun') > 0:
		dryRun = True
except ValueError:
	pass

def timestamp():
	ts = time.time()
	return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

bot = Poloniex(config.get("API","apikey"), config.get("API","secret"))
log = Logger()

#total lended global variable
totalLended = {}

def refreshTotalLended():
        global totalLended
	cryptoLended = bot.returnActiveLoans()

	totalLended = {}
	cryptoLendedSum = Decimal(0)

	for item in cryptoLended["provided"]:
		itemStr = item["amount"].encode("utf-8")
		itemFloat = Decimal(itemStr)
		if item["currency"] in totalLended:
			cryptoLendedSum = totalLended[item["currency"]] + itemFloat
			totalLended[item["currency"]] = cryptoLendedSum
		else:
			cryptoLendedSum = itemFloat
			totalLended[item["currency"]] = cryptoLendedSum

def stringifyTotalLended():
	result = 'Lended: '
	for key in sorted(totalLended):
		result += '[' + "%.3f" % Decimal(totalLended[key]) + ' '
		result += key + '] '
	return result

def createLoanOffer(cur,amt,rate):
	days = '2'
	#if (minDailyRate - 0.000001) < rate and Decimal(amt) > 0.001:
	if float(amt) > 0.001:
		rate = float(rate) - 0.000001 #lend offer just bellow the competing one
		amt = "%.8f" % Decimal(amt)
		if rate > sixtyDayThreshold:
			days = '60'
		if sixtyDayThreshold == 0:
			days = '2'
		if dryRun == False:
			msg = bot.createLoanOffer(cur,amt,days,0,rate)
			log.offer(amt, cur, rate, days, msg)

def cancelAndLoanAll():
	loanOffers = bot.returnOpenLoanOffers('BTC') #some bug with api wrapper? no idea why I have to provide a currency, and then receive every other
	if type(loanOffers) is list: #silly api wrapper, empty dict returns a list, which brakes the code later.
		loanOffers = {}
	if loanOffers.get('error'):
		print loanOffers.get('error')
		print 'You might want to edit config file (default.cnf) and put correct apisecret and key values'
		exit(1)

	onOrderBalances = {}
	for cur in loanOffers:
		for offer in loanOffers[cur]:
			onOrderBalances[cur] = onOrderBalances.get(cur, 0) + Decimal(offer['amount'])
			if dryRun == False:
				msg = bot.cancelLoanOffer(cur,offer['id'])
				log.cancelOrders(cur, msg)

	lendingBalances = bot.returnAvailableAccountBalances("lending")['lending']
	if dryRun == True: #just fake some numbers, if dryrun (testing)
		if type(lendingBalances) is list: #silly api wrapper, empty dict returns a list, which brakes the code later.
			lendingBalances = {}
		lendingBalances.update(onOrderBalances)

	for activeCur in lendingBalances:

		activeBal = lendingBalances[activeCur]

		#min daily rate can be changed per currency
		curMinDailyRate = minDailyRate
		if activeCur in coincfg:
			if coincfg[activeCur]['maxactive'] == 0:
				log.log('maxactive amount for ' + activeCur + ' set to 0, won\'t lend.')
				continue
			curMinDailyRate = coincfg[activeCur]['minrate']
			log.log('Using custom mindailyrate ' + str(coincfg[activeCur]['minrate']*100) + '% for ' + activeCur)

		loans = bot.returnLoanOrders(activeCur)
		s = Decimal(0) #sum
		i = int(0) #offer book iterator
		j = int(0) #spread step count
		lent = Decimal(0)
		step = (gapTop - gapBottom)/spreadLend
		#TODO check for minimum lendable amount, and try to decrease the spread. e.g. at the moment balances lower than 0.001 won't be lent
		#in case of empty lendbook, lend at max
                activePlusLended = Decimal(activeBal)
                if activeCur in totalLended:
                        activePlusLended += Decimal(totalLended[activeCur])
		if len(loans['offers']) == 0:
			createLoanOffer(activeCur,Decimal(activeBal)-lent,maxDailyRate)
		for offer in loans['offers']:
			s = s + Decimal(offer['amount'])
			s2 = s
			while True:
				if s2 > activePlusLended*(gapBottom/100+(step/100*j)) and Decimal(offer['rate']) > curMinDailyRate:
					j += 1
					s2 = s2 + Decimal(activeBal)/spreadLend
				else:
					createLoanOffer(activeCur,s2-s,offer['rate'])
					lent = lent + (s2-s).quantize(SATOSHI)
					break
				if j == spreadLend:
					createLoanOffer(activeCur,Decimal(activeBal)-lent,offer['rate'])
	                                break
			if j == spreadLend:
				break
			i += 1
			if i == len(loans['offers']): #end of the offers lend at max
				createLoanOffer(activeCur,Decimal(activeBal)-lent,maxDailyRate)

log.log('Welcome to Poloniex Lending Bot')

while True:
	try:
                refreshTotalLended()
		log.refreshStatus(stringifyTotalLended())
		cancelAndLoanAll()
        except Exception as e:
                log.log("ERROR: " + str(e))
		pass
	except KeyboardInterrupt:
		print '\nbye'
		exit(0)
        time.sleep(sleepTime)
