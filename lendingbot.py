import io, sys, time, datetime, urllib2
from poloniex import Poloniex
from ConfigParser import SafeConfigParser
from Logger import Logger

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
mindailyrate = 0.04
#max rate. 2% is good choice because it's default at margin trader interface. 5% is max to be accepted by the exchange
maxdailyrate = 2
#The number of offers to split the available balance uniformly across the [gaptop, gapbottom] range.
spreadlend = 3
#The depth of lendbook (in percent of lendable balance) to move through before placing the first (gapbottom) and last (gaptop) offer.
#if gapbottom is set to 0, the first offer will be at the lowest possible rate. However some low value is recommended (say 10%) to skip dust offers
gapbottom = 10
gaptop = 200
#Daily lend rate threshold after which we offer lends for 60 days as opposed to 2. If set to 0 all offers will be placed for a 2 day period
sixtydaythreshold = 0.2
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
minDailyRate = float(config.get("BOT","mindailyrate"))/100
maxDailyRate = float(config.get("BOT","maxdailyrate"))/100
spreadLend = int(config.get("BOT","spreadlend"))
gapBottom = float(config.get("BOT","gapbottom"))
gapTop = float(config.get("BOT","gaptop"))
sixtyDayThreshold = float(config.get("BOT","sixtydaythreshold"))/100

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

def totalLended():
	cryptoLended = bot.returnActiveLoans()

	allPairs = {}
	cryptoLendedSum = float(0)

	for item in cryptoLended["provided"]:
		itemStr = item["amount"].encode("utf-8")
		itemFloat = float(itemStr)
		if item["currency"] in allPairs:
			cryptoLendedSum = allPairs[item["currency"]] + itemFloat
			allPairs[item["currency"]] = cryptoLendedSum
		else:
			cryptoLendedSum = itemFloat
			allPairs[item["currency"]] = cryptoLendedSum
	result = ''
	for key in sorted(allPairs):
		result += '[' + "%.2f" % float(allPairs[key]) + ' '
		result += key + '] '
	return result

def createLoanOffer(cur,amt,rate):
	days = '2'
	if (minDailyRate - 0.000001) < rate and float(amt) > 0.001:
		rate = float(rate) - 0.000001 #lend offer just bellow the competing one
		amt = "%.8f" % float(amt)
		if rate > sixtyDayThreshold:
			days = '60'
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
			onOrderBalances[cur] = onOrderBalances.get(cur, 0) + float(offer['amount'])
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

		loans = bot.returnLoanOrders(activeCur)
		s = float(0) #sum
		i = int(0) #offer book iterator
		j = int(0) #spread step count
		lent = float(0)
		step = (gapTop - gapBottom)/spreadLend
		#TODO check for minimum lendable amount, and try to decrease the spread. e.g. at the moment balances lower than 0.001 won't be lent
		for offer in loans['offers']:
			s = s + float(offer['amount'])
			s2 = s
			while True:
				if s2 > float(activeBal)*(gapBottom/100+(step/100*j)) and float(offer['rate']) > minDailyRate:
					j += 1
					#ran into a problem were 14235.82451057 couldn't be lent because of rounding
					s2 = s2 + float(activeBal)/spreadLend - 0.00000001
				else:
					createLoanOffer(activeCur,s2-s,offer['rate'])
					lent = lent + (s2-s)
					break
				if j == spreadLend:
					createLoanOffer(activeCur,float(activeBal)-lent,offer['rate'])
	                                break
			if j == spreadLend:
				break
			i += 1
			if i == len(loans['offers']): #end of the offers lend at max
				createLoanOffer(activeCur,float(activeBal)-lent,maxDailyRate)

log.log('Welcome to Poloniex Lending Bot')

while True:
	try:
		log.refreshStatus(totalLended())
		cancelAndLoanAll()
		time.sleep(sleepTime)
	except (urllib2.HTTPError, urllib2.URLError) as error:
        	print "ERROR: " + error
		pass
	except KeyboardInterrupt:
		print '\nbye'
		exit(0)
