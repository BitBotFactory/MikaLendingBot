import io, sys, time, datetime, urllib2, json, argparse 
import traceback
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
#sleep between active iterations, time in seconds (1-3600)
sleeptimeactive = 60

#sleep between inactive iterations, time in seconds (1-3600)
#set to same as sleeptimeactive to disable
sleeptimeinactive = 300

#minimum daily lend rate in percent (0.00003-0.05)
mindailyrate = 0.04

#max rate. 2% is good choice because it's default at margin trader interface.
#5% is max to be accepted by the exchange (0.00003-0.05)
maxdailyrate = 2

#The number of offers to split the available balance across the [gaptop, gapbottom] range. (1-20)
spreadlend = 3

#The depth of lendbook (in percent of lendable balance) to move through
#before placing the first (gapbottom) and last (gaptop) offer.
#If gapbottom is set to 0, the first offer will be at the lowest possible rate.
#However some low value is recommended (say 10%) to skip dust offers.
gapbottom = 10
gaptop = 200

#Daily lend rate threshold after which we offer lends for 60 days as opposed to 2.
#If set to 0 all offers will be placed for a 2 day period (0.00003-0.05)
sixtydaythreshold = 0.2

#Minimum loan size the minimum size of offers to make, bigger values prevent the bot from loaning small available amounts but reduce loans fragmentation
minloansize = 0.001

#AutoRenew - if set to 1 the bot will set the AutoRenew flag for the loans when you stop it (Ctrl+C) and clear the AutoRenew flag when on started
autorenew = 0

#custom config per coin, useful when closing positions etc.
#syntax: ["COIN:mindailyrate:maxactiveamount",...]
#if maxactive amount is 0 - stop lending this coin. in the future you'll be able to limit amount to be lent.
#coinconfig = ["BTC:0.18:1","CLAM:0.6:1"]

#this option creates a json log file instead of console output which includes the most recent status
#uncomment both jsonfile and jsonlogsize to enable
#jsonfile = www/botlog.json
#limits the amount of log lines to save
#jsonlogsize = 200
#enables a webserver for the www folder, in order to easily use the lendingbot.html with the json log
#startWebServer = true
"""

#Defaults
minLoanSize = 0.001

parser = argparse.ArgumentParser() #Start args.
parser.add_argument("-cfg", "--config", help="Location of custom configuration file, overrides settings below")
parser.add_argument("-dry", "--dryrun", help="Make pretend orders", action="store_true")
parser.add_argument("-clrrenew", "--clearautorenew", help="Stops all autorenew orders", action="store_true")
parser.add_argument("-setrenew", "--setautorenew", help="Sets all orders to autorenew", action="store_true")
parser.add_argument("-key", "--apikey", help="Account API key, should be unique to this script.")
parser.add_argument("-secret", "--apisecret", help="Account API secret, should be unique to this script.")
parser.add_argument("-sleepactive", "--sleeptimeactive", help="Time between active iterations, seconds")
parser.add_argument("-sleepinactive", "--sleeptimeinactive", help="Time between inactive iterations, seconds")
parser.add_argument("-minrate", "--mindailyrate", help="Minimum rate you will lend at")
parser.add_argument("-maxrate", "--maxdailyrate", help="Maximum rate you will lend at")
parser.add_argument("-spread", "--spreadlend", help="How many orders to split your lending into")
parser.add_argument("-gapbot", "--gapbottom", help="Percentage of your order's volume into the ledger you start lending")
parser.add_argument("-gaptop", "--gaptop", help="Percentage of your order's volume into the ledger you stop lending")
parser.add_argument("-60day", "--sixtydaythreshold", help="Rate at where bot will request to lend for 60 days")
parser.add_argument("-autorenew", "--autorenew", help="Sets autorenew on bot stop, and clears autorenew on start", action="store_true")
parser.add_argument("-minloan", "--minloansize", help='Minimum size of offers to make')
parser.add_argument("-json", "--jsonfile", help="Location of .json file to save log to")
parser.add_argument("-jsonsize", "--jsonlogsize", help="How many lines to keep saved to the json log file")
parser.add_argument("-server", "--startwebserver", help="If enabled, starts a webserver for the /www/ folder on 127.0.0.1:8000/lendingbot.html", action="store_true")
parser.add_argument("-coincfg", "--coinconfig", help='Custom config per coin, useful when closing positions etc. Syntax: COIN:mindailyrate:maxactiveamount,COIN2:min2:maxactive2,...')
args = parser.parse_args() #End args.
#Start handling args.
if args.apikey:
	apiKey = args.apikey
if args.apisecret:
	apiSecret = args.apisecret
if args.sleeptimeactive:
	sleepTimeActive = int(args.sleeptimeactive)
if args.sleeptimeinactive:
	sleepTimeInactive = int(args.sleeptimeinactive)
if args.mindailyrate:
	minDailyRate = Decimal(args.mindailyrate)/100
if args.maxdailyrate:
	maxDailyRate = Decimal(args.maxdailyrate)/100
if args.spreadlend:
	spreadLend = int(args.spreadlend)
if args.gapbottom:
	gapBottom = Decimal(args.gapbottom)
if args.gaptop:
	gapTop = Decimal(args.gapbottom)
if args.sixtydaythreshold:
	sixtyDayThreshold = Decimal(args.sixtydaythreshold)/100
if args.dryrun:
	dryRun = True
else:
	dryRun = False
if args.config:
	config_location = args.config
if args.autorenew:
	autoRenew = 1
else:
	autoRenew = 0
if args.minloansize:
	minLoanSize = Decimal(args.minloansize)
coincfg = {}
if args.coinconfig:
	coinconfig = args.coinconfig.split(',')
	for cur in coinconfig:
		cur = cur.split(':')
		coincfg[cur[0]] = dict(minrate=(Decimal(cur[1]))/100, maxactive=Decimal(cur[2]))
#End handling args.

#Check if we need a config file at all (If all settings are passed by args, we won't)
if args.apikey and args.apisecret and args.sleeptimeactive and args.sleeptimeinactive and args.mindailyrate and args.maxdailyrate and args.spreadlend and args.gapbottom and args.gaptop and args.sixtydaythreshold:
	#If all that was true, we don't need a config file...
	config_needed = False
	print "Settings met from arguments."
else:
	config_needed = True
	print "Obtaining settings from config file."

#When true, will overwrite anything passed by args with the found cfg
if config_needed: 
	loadedFiles = config.read([config_location])
	# Create default config file if not found
	if len(loadedFiles) != 1:
		config.readfp(io.BytesIO(defaultconfig))
		with open(config_location, "w") as configfile:
			configfile.write(defaultconfig)
			print 'Edit default.cfg file with your api key and secret values'
			exit(0)

	try:
		sleepTimeActive = float(config.get("BOT","sleeptimeactive"))
		sleepTimeInactive = float(config.get("BOT","sleeptimeinactive"))
	except:
		sleepTime = float(config.get("BOT","sleeptime")) #If it can't find a setting, run with the old cfg.
		sleepTimeActive = sleepTime
		sleepTimeInactive = sleepTime
		print "!!! Please update to new config that includes Inactive Mode. !!!" #Update alert.
	apiKey = config.get("API","apikey")
	apiSecret = config.get("API","secret")
	minDailyRate = Decimal(config.get("BOT","mindailyrate"))/100
	maxDailyRate = Decimal(config.get("BOT","maxdailyrate"))/100
	spreadLend = int(config.get("BOT","spreadlend"))
	gapBottom = Decimal(config.get("BOT","gapbottom"))
	gapTop = Decimal(config.get("BOT","gaptop"))
	sixtyDayThreshold = float(config.get("BOT","sixtydaythreshold"))/100
	autorenew = int(config.get("BOT","autorenew"))
	if(config.has_option('BOT', 'minloansize')):
		minLoanSize = Decimal(config.get("BOT",'minloansize'))
	
	try:
		#parsed
		coinconfig = (json.loads(config.get("BOT","coinconfig")))
		for cur in coinconfig:
			cur = cur.split(':')
			coincfg[cur[0]] = dict(minrate=(Decimal(cur[1]))/100, maxactive=Decimal(cur[2]))
	except Exception as e:
		pass
sleepTime = sleepTimeActive #Start with active mode
#sanity checks
if sleepTime < 1 or sleepTime > 3600 or sleepTimeInactive < 1 or sleepTimeInactive > 3600:
	print "sleeptime values must be 1-3600"
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


def timestamp():
	ts = time.time()
	return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

bot = Poloniex(apiKey, apiSecret)
log = {}

# check if json output is enabled
jsonOutputEnabled = (config.has_option('BOT', 'jsonfile') and config.has_option('BOT', 'jsonlogsize')) or (args.jsonfile and args.jsonlogsize) 
if jsonOutputEnabled:
	if config_needed:
		jsonFile = config.get("BOT","jsonfile")
		jsonLogSize = int(config.get("BOT","jsonlogsize"))
	else:
		jsonFile = args.jsonfile
		jsonLogSize = args.jsonlogsize
	log = Logger(jsonFile, jsonLogSize)
else:
	log = Logger()

#total lended global variable
totalLended = {}

def refreshTotalLended():
	global totalLended, rateLended
	cryptoLended = bot.returnActiveLoans()

	totalLended = {}
	rateLended = {}
	cryptoLendedSum = Decimal(0)
	cryptoLendedRate = Decimal(0)

	for item in cryptoLended["provided"]:
		itemStr = item["amount"].encode("utf-8")
		itemFloat = Decimal(itemStr)
		itemRateStr = item["rate"].encode("utf-8")
		itemRateFloat = Decimal(itemRateStr)
		if item["currency"] in totalLended:
			cryptoLendedSum = totalLended[item["currency"]] + itemFloat
			cryptoLendedRate = rateLended[item["currency"]] + (itemRateFloat * itemFloat)
			totalLended[item["currency"]] = cryptoLendedSum
			rateLended[item["currency"]] = cryptoLendedRate
		else:
			cryptoLendedSum = itemFloat
			cryptoLendedRate = itemRateFloat * itemFloat
			totalLended[item["currency"]] = cryptoLendedSum
			rateLended[item["currency"]] = cryptoLendedRate

def stringifyTotalLended():
	result = 'Lended: '
	for key in sorted(totalLended):
		averageLendingRate = Decimal(rateLended[key]*100/totalLended[key])
		result += '[%.4f %s @ %.4f%%] ' % (Decimal(totalLended[key]), key, averageLendingRate)
		log.updateStatusValue(key, "lentSum", totalLended[key])
		log.updateStatusValue(key, "averageLendingRate", averageLendingRate)
	return result

def createLoanOffer(cur,amt,rate):
	days = '2'
	#if (minDailyRate - 0.000001) < rate and Decimal(amt) > minLoanSize:
	if float(amt) > minLoanSize:
		rate = float(rate) - 0.000001 #lend offer just bellow the competing one
		amt = "%.8f" % Decimal(amt)
		if rate > sixtyDayThreshold:
			days = '60'
		if sixtyDayThreshold == 0:
			days = '2'
		if dryRun == False:
			msg = bot.createLoanOffer(cur,amt,days,0,rate)
			log.offer(amt, cur, rate, days, msg)

#limit of orders to request
loanOrdersRequestLimit = {}
defaultLoanOrdersRequestLimit = 200

def cancelAndLoanAll():
	loanOffers = bot.returnOpenLoanOffers()
	if type(loanOffers) is list: #silly api wrapper, empty dict returns a list, which brakes the code later.
		loanOffers = {}
	if loanOffers.get('error'):
		print loanOffers.get('error')
		print 'You might want to edit config file (default.cfg) and put correct apisecret and key values'
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
	
	activeCurIndex = 0
	usableCurrencies = 0
	global sleepTime #We need global var to edit sleeptime
	while activeCurIndex < len(lendingBalances):
		activeCur = lendingBalances.keys()[activeCurIndex]
		activeCurIndex += 1
		activeBal = lendingBalances[activeCur]
		if float(activeBal) > minLoanSize: #Check if any currencies have enough to lend, if so, make sure sleeptimer is set to active.
			usableCurrencies = 1
		
		#min daily rate can be changed per currency
		curMinDailyRate = minDailyRate
		if activeCur in coincfg:
			if coincfg[activeCur]['maxactive'] == 0:
				log.log('maxactive amount for ' + activeCur + ' set to 0, won\'t lend.')
				continue
			curMinDailyRate = coincfg[activeCur]['minrate']
			log.log('Using custom mindailyrate ' + str(coincfg[activeCur]['minrate']*100) + '% for ' + activeCur)

		# make sure we have a request limit for this currency
		if(activeCur not in loanOrdersRequestLimit):
			loanOrdersRequestLimit[activeCur] = defaultLoanOrdersRequestLimit
			
		loans = bot.returnLoanOrders(activeCur, loanOrdersRequestLimit[activeCur] )
		loansLength = len(loans['offers'])

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
		#log total coin
		log.updateStatusValue(activeCur, "totalCoins", activePlusLended)
		if loansLength == 0:
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
			if (i == loansLength): #end of the offers
				if(loansLength < loanOrdersRequestLimit[activeCur]):
					#lend at max
					createLoanOffer(activeCur,Decimal(activeBal)-lent,maxDailyRate)
				else:
					# increase limit for currency to get a more accurate response
					loanOrdersRequestLimit[activeCur] += defaultLoanOrdersRequestLimit
					log.log( activeCur + ': Not enough offers in response, adjusting request limit to ' + str(loanOrdersRequestLimit[activeCur]))
					# repeat currency
					activeCurIndex -= 1
	if usableCurrencies == 0: #After loop, if no currencies had enough to lend, use inactive sleep time.
		sleepTime = sleepTimeInactive
	else: #Else, use active sleep time.
		sleepTime = sleepTimeActive
def setAutoRenew(auto):
	i = int(0) #counter
	try:
		action = 'Clearing'
		if(auto == 1):
			action = 'Setting'
		log.log(action + ' AutoRenew...(Please Wait)')
		cryptoLended = bot.returnActiveLoans()
		loansCount = len(cryptoLended["provided"])
		for item in cryptoLended["provided"]:
			if int(item["autoRenew"]) != auto:
				log.refreshStatus('Processing AutoRenew - ' + str(i) + ' of ' + str(loansCount) + ' loans')
				bot.toggleAutoRenew(int(item["id"]))
				i += 1
	except KeyboardInterrupt:
		log.log('Toggled AutoRenew for ' +  str(i) + ' loans')
		raise SystemExit
	log.log('Toggled AutoRenew for ' +  str(i) + ' loans')

server = None
def startWebServer():
	import SimpleHTTPServer
	import SocketServer
	import os

	try:
		PORT = 8000
		HOST = '127.0.0.1'

		class QuietHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
			# quiet server logs
			def log_message(self, format, *args):
				return
			# serve from www folder under current working dir
			def translate_path(self, path):
				return SimpleHTTPServer.SimpleHTTPRequestHandler.translate_path(self, '/www' + path)
		
		global server
		server = SocketServer.TCPServer((HOST, PORT), QuietHandler)
		print 'Started WebServer, lendingbot status available at http://'+ HOST +':' + str(PORT) + '/lendingbot.html'
		server.serve_forever()
	except Exception as e:
		print 'Failed to start WebServer' + str(e)
		
def updateConversionRates():
	global jsonOutputEnabled, totalLended
	if(jsonOutputEnabled):
		tickerResponse = bot.returnTicker();
		for couple in tickerResponse:
			currencies = couple.split('_')
			ref = currencies[0]
			currency = currencies[1]
			if ref == 'BTC' and currency in totalLended:
				log.updateStatusValue(currency, 'highestBid', tickerResponse[couple]['highestBid'])
				log.updateStatusValue(currency, 'couple', couple)
		
#Parse these down here...
if args.clearautorenew:
	setAutoRenew(0)
	raise SystemExit
if args.setautorenew:
	setAutoRenew(1)
	raise SystemExit

def stopWebServer():
	try:
		print "Stopping WebServer"
		server.shutdown();
	except Exception as e:
		print 'Failed to stop WebServer' + str(e)
	
print 'Welcome to Poloniex Lending Bot'

if config_needed:
	webServerEnabled = config.has_option('BOT', 'startWebServer') and config.getboolean('BOT', 'startWebServer')
else:
	webServerEnabled = args.startwebserver
if webServerEnabled:
	import threading
	thread = threading.Thread(target = startWebServer)
	thread.deamon = True
	thread.start()

#if config includes autorenew - start by clearing the current loans
if autoRenew == 1:
	setAutoRenew(0);

try:
	while True:
		try:
			refreshTotalLended()
			updateConversionRates()
			cancelAndLoanAll()
			log.refreshStatus(stringifyTotalLended())
			log.persistStatus()
			time.sleep(sleepTime)
		except Exception as e:
			log.log("ERROR: " + str(e))
			traceback.print_exc()
			log.persistStatus()
			time.sleep(sleepTime)
			pass
except KeyboardInterrupt:
	if autoRenew == 1:
		setAutoRenew(1);
	if webServerEnabled:
		stopWebServer()
	log.log('bye')
	exit(0)
