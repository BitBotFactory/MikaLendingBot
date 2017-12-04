from flask_wtf import Form
from wtforms import StringField, BooleanField, IntegerField, FloatField, DateField
from wtforms.validators import DataRequired


class BotConfig(Form):
    label = StringField('label', validators=[DataRequired()])
    sleeptimeactive = IntegerField('sleeptimeactive', validators=[DataRequired()])
    sleeptimeinactive = IntegerField('sleeptimeinactive', validators=[DataRequired()])
    timeout = IntegerField('timeout', validators=[DataRequired()])
    mindailyrate = IntegerField('mindailyrate', validators=[DataRequired()])
    maxdailyrate = IntegerField('maxdailyrate', validators=[DataRequired()])
    spreadlend = IntegerField('spreadlend', validators=[DataRequired()])
    gapmode = StringField('gapmode')
    gapbottom = IntegerField('gapbottom', validators=[DataRequired()])
    gaptop = IntegerField('gaptop', validators=[DataRequired()])
    xdaythreshold = IntegerField('xdaythreshold', validators=[DataRequired()])
    xdays = IntegerField('xdays', validators=[DataRequired()])
    xday_spread = IntegerField('xday_spread', validators=[DataRequired()])
    transferableCurrencies = StringField('transferableCurrencies')
    minloansize = IntegerField('minloansize', validators=[DataRequired()])
    keepstuckorders = BooleanField('keepstuckorders')
    hideCoins = BooleanField('hideCoins')
    end_date = DateField(format='%Y,%m,%d', validators=[DataRequired()])
    maxtolend = IntegerField('maxtolend', validators=[DataRequired()])
    maxpercenttolend = IntegerField('maxpercenttolend', validators=[DataRequired()])
    maxtolendrate = IntegerField('maxtolendrate', validators=[DataRequired()])
    web_server_enabled = BooleanField('web_server_enabled')
    jsonfile = StringField('jsonfile')
    jsonlogsize = IntegerField('jsonlogsize', validators=[DataRequired()])
    json_output_enabled = BooleanField('json_output_enabled')
    startwebserver = BooleanField('startWebServer')
    customwebserveraddress = StringField('customWebServerAddress')
    customwebserverport = IntegerField('customWebServerPort', validators=[DataRequired()])
    customwebservertemplate = StringField('customWebServerTemplate')
    outputCurrency = StringField('outputCurrency')
    plugins = StringField('plugins')


class ApiConfig(Form):
    exchange = StringField('exchange', validators=[DataRequired()])
    apikey = StringField('apikey', validators=[DataRequired()])
    secret = StringField('secret', validators=[DataRequired()])


class MarketAnalysisConfig(Form):
    ma_debug_log = BooleanField('ma_debug_log')
    analyseCurrencies = StringField('analyseCurrencies')


class NotificationsConfig(Form):
    notify_conf = StringField('plugins')
