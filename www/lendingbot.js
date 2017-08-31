// vim: ts=4:sw=4:et

var localFile, reader;

var Hour = new Timespan("Hour", 1/24);
var Day = new Timespan("Day", 1);
var Week = new Timespan("Week", 7);
var Month = new Timespan("Month", 30);
var Year = new Timespan("Year", 365);
var refreshRate = 30;
var timespans = [];
var summaryCoinRate, summaryCoin;
var earningsOutputCoinRate, earningsOutputCoin;
var outputCurrencyDisplayMode = 'all'
var validOutputCurrencyDisplayModes = ['all', 'summary'];
var effRateMode = 'lentperc';
var validEffRateModes = ['lentperc', 'onlyfee'];

// BTC DisplayUnit
var BTC = new BTCDisplayUnit("BTC", 1);
var mBTC = new BTCDisplayUnit("mBTC", 1000);
var Bits = new BTCDisplayUnit("Bits", 1000000);
var Satoshi = new BTCDisplayUnit("Satoshi", 100000000);
var displayUnit = BTC;
var btcDisplayUnitsModes = [BTC, mBTC, Bits, Satoshi];

function updateJson(data) {
    $('#status').text(data.last_status);
    $('#updated').text(data.last_update);
    $('#title').text(data.exchange + ' ' + data.label)
    document.title = data.exchange + ' ' + data.label

    var rowCount = data.log.length;
    var table = $('#logtable');
    table.empty();
    for (var i = rowCount - 1; i >=0; i--) {
        table.append($('<tr/>').append($('<td colspan="2" />').text(data.log[i])));
    }

    updateOutputCurrency(data.outputCurrency);
    updateRawValues(data.raw_data);
    updateNavbar(data.plugins);
}

function updateNavbar(plugins) {

    // No plugins enabled. Nothing to do.
    if (plugins == undefined || plugins.enabled == undefined)
        return;

    var enabled = plugins.enabled
    var navbar = $('#navbar-menu')
    var navbarItems = Array()

    // Build list of navbar items
    $.each($('#navbar-menu li'), function() {
        if ($(this).attr('id') != undefined) {
            navbarItems.push($(this).attr('id').toLowerCase())
        }
    });

    // iterate through enabled plugins; look for 'navbar': true
    $.each(enabled, function(i, val) {
        var v = val.toLowerCase()
        if ((v in plugins) && ('navbar' in plugins[v]) && (plugins[v]['navbar'])) {

            // this plugin wants a link in the navbar.
            // Search current navbar and add if needed
            var newId = v + "-navbar"
            if (navbarItems.indexOf(newId) < 0) {
                var newItem = '<li id="' + newId + '" data-toggle="collapse" data-target=".navbar-collapse.in">'
                newItem += '<a href="' + v + '.html">' + val + '</a></li>'
                navbar.prepend(newItem);
            }
        }
    });
}

function updateOutputCurrency(outputCurrency){
    var OutCurr = Object.keys(outputCurrency);
    summaryCoin = outputCurrency['currency'];
    summaryCoinRate = parseFloat(outputCurrency['highestBid']);
    // switch between using outputCoin for summary only or all lending coins earnings
    if(outputCurrencyDisplayMode == 'all') {
        earningsOutputCoin = summaryCoin;
        earningsOutputCoinRate = summaryCoinRate;
    } else {
        earningsOutputCoin = 'BTC'
        earningsOutputCoinRate = 1;
    }
}

// prints a pretty float with accuracy.
// above zero accuracy will be used for float precision
// below zero accuracy will indicate precision after must significat digit
// strips trailing zeros
function prettyFloat(value, accuracy) {
    var precision = Math.round(Math.log10(value));
    var result = precision < 0 ? value.toFixed(Math.min((accuracy - precision), 8)) : value.toFixed(accuracy);
    return isNaN(result) ? '0' : result.replace(/(?:\.0+|(\.\d+?)0+)$/, '$1');
}

function printFloat(value, precision) {
    var multiplier = Math.pow(10, precision);
    var result = Math.round(value * multiplier) / multiplier;
    return result = isNaN(result) ? '0' : result.toFixed(precision);
}

function updateRawValues(rawData){
    var table = document.getElementById("detailsTable");
    table.innerHTML = "";
    var currencies = Object.keys(rawData);
    var totalBTCEarnings = {};
    for (var keyIndex = 0; keyIndex < currencies.length; ++keyIndex)
    {
        var currency = currencies[keyIndex];
        var btcMultiplier = currency == 'BTC' ? displayUnit.multiplier : 1;
        var averageLendingRate = parseFloat(rawData[currency]['averageLendingRate']);
        var lentSum = parseFloat(rawData[currency]['lentSum']);
        var totalCoins = parseFloat(rawData[currency]['totalCoins']);
        var maxToLend = parseFloat(rawData[currency]['maxToLend']);
        var highestBidBTC = parseFloat(rawData[currency]['highestBid']);

        if (currency == 'BTC') {
            // no bids for BTC provided by poloniex
            // this is added so BTC can be handled like other coins for conversions
            highestBidBTC = 1;
        }
        var couple = rawData[currency]['couple'];

        if (!isNaN(averageLendingRate) && !isNaN(lentSum) || !isNaN(totalCoins))
        {

            // cover cases where totalCoins isn't updated because all coins are lent
            if (isNaN(totalCoins) && !isNaN(lentSum)) {
                totalCoins = lentSum;
            }
            var rate = +averageLendingRate  * 0.85 / 100; // 15% goes to exchange fees

            var earnings = '';
            var earningsSummaryCoin = '';
            timespans.forEach(function(timespan) {
                // init totalBTCEarnings
                if (isNaN(totalBTCEarnings[timespan.name])) {
                    totalBTCEarnings[timespan.name] = 0;
                }

                // calculate coin earnings
                timespanEarning = timespan.calcEarnings(lentSum, rate);
                earnings += timespan.formatEarnings(currency, timespanEarning, true);

                // sum BTC earnings for all coins
                if(!isNaN(highestBidBTC)) {
                    timespanEarningBTC = timespan.calcEarnings(lentSum * highestBidBTC, rate);
                    totalBTCEarnings[timespan.name] += timespanEarningBTC;
                    if(currency != earningsOutputCoin) {
                        earningsSummaryCoin += timespan.formatEarnings(earningsOutputCoin, timespanEarningBTC * earningsOutputCoinRate);
                    }
                }

            });

            var effRateModePerc = 1;
            if (effRateMode == 'lentperc')
                effRateModePerc = lentSum / totalCoins;
            var effectiveRate = rate * 100 * effRateModePerc;
            var yearlyRate = rate * 100 * 365 * effRateModePerc; // no reinvestment
            var yearlyRateComp = (Math.pow(rate + 1, 365) - 1) * 100 * effRateModePerc; // with daily reinvestment

            var lentPerc = lentSum / totalCoins * 100;
            var lentPercLendable = lentSum / maxToLend * 100;
            function makeTooltip(title, text) {
                return '&nbsp;<a data-toggle="tooltip" class="plb-tooltip" title="' + title + '">' + text + '</a>';
            }
            var avgRateText = makeTooltip("Average loan rate, simple average calculation of active loans rates.", "Avg.");
            var effRateText;
            if (effRateMode == 'lentperc')
                effRateText = makeTooltip("Effective loan rate, considering lent precentage and exchange 15% fee.", "Eff.");
            else
                effRateText = makeTooltip("Effective loan rate, considering exchange 15% fee.", "Eff.");
            var compoundRateText = makeTooltip("Compound rate, the result of reinvesting the interest.", "Comp.");
            var lentStr = 'Lent ' + printFloat(lentSum * btcMultiplier, 4) +' of ' + printFloat(totalCoins * btcMultiplier, 4) + ' (' + printFloat(lentPerc, 2) + '%)';

            if (totalCoins != maxToLend) {
                lentStr += ' <b>Total</b><br/>Lent ' + printFloat(lentSum * btcMultiplier, 4) + ' of ' + printFloat(maxToLend * btcMultiplier, 4) + ' (' + printFloat(lentPercLendable, 2) + '%) <b>Lendable</b>';
            }

            var displayCurrency = currency == 'BTC' ? displayUnit.name : currency;
            var currencyStr = "<b>" + displayCurrency + "</b>";
            if(!isNaN(highestBidBTC) && earningsOutputCoin != currency) {
                currencyStr += "<br/>1 "+ displayCurrency + " = " + prettyFloat(earningsOutputCoinRate * highestBidBTC / btcMultiplier , 2) + ' ' + earningsOutputCoin;
            }
            var rowValues = [currencyStr, lentStr,
                "<div class='inlinediv' >" + printFloat(averageLendingRate, 5) + '% Day' + avgRateText + '<br/>'
                    + printFloat(effectiveRate, 5) + '% Day' + effRateText + '<br/></div>'
                    + "<div class='inlinediv' >" + printFloat(yearlyRate, 2) + '% Year<br/>'
                    +  printFloat(yearlyRateComp, 2) + '% Year' + compoundRateText + "</div>" ];

            // print coin status
            var row = table.insertRow();
            for (var i = 0; i < rowValues.length; ++i) {
                var cell = row.appendChild(document.createElement("td"));
                cell.innerHTML = rowValues[i];
                cell.style.verticalAlign = "text-top";
                if (i == 0) {
                    cell.setAttribute("width", "20%");
                }
            }
            $(row).find('[data-toggle="tooltip"]').tooltip();

            var earningsColspan = rowValues.length - 1;
            // print coin earnings
            var row = table.insertRow();
            if (lentSum > 0) {
                var cell1 = row.appendChild(document.createElement("td"));
                cell1.innerHTML = "<span class='hidden-xs'>"+ displayCurrency +"<br/></span>Est. "+ compoundRateText +"<br/>Earnings";
                var cell2 = row.appendChild(document.createElement("td"));
                cell2.setAttribute("colspan", earningsColspan);
                if (earningsSummaryCoin != '') {
                    cell2.innerHTML = "<div class='inlinediv' >" + earnings + "<br/></div><div class='inlinediv' style='padding-right:0px'>"+ earningsSummaryCoin + "</div>";
                } else {
                    cell2.innerHTML = "<div class='inlinediv' >" + earnings + "</div>";
                }
            }
        }
    }

    // add headers
    var thead = table.createTHead();

    // show account summary
    if (currencies.length > 1 || summaryCoin != earningsOutputCoin) {
        earnings = '';
        timespans.forEach(function(timespan) {
            earnings += timespan.formatEarnings( summaryCoin, totalBTCEarnings[timespan.name] * summaryCoinRate);
        });
        var row = thead.insertRow(0);
        var cell = row.appendChild(document.createElement("th"));
        cell.innerHTML = "Account<br/>Estimated<br/>Earnings";
        cell.style.verticalAlign = "text-top";
        cell = row.appendChild(document.createElement("th"));
        cell.setAttribute("colspan", 2);
        cell.innerHTML = earnings;
    }
}

function handleLocalFile(file) {
    localFile = file;
    reader = new FileReader();
    reader.onload = function(e) {
        updateJson(JSON.parse(reader.result));
    };
    reader.readAsText(localFile, 'utf-8');
}

function loadData() {
    if (localFile) {
        reader.readAsText(localFile, 'utf-8');
        setTimeout('loadData()', refreshRate * 1000)
    } else {
        // expect the botlog.json to be in the same folder on the webserver
        var file = 'botlog.json';
        $.getJSON(file, function (data) {
            updateJson(data);
            // reload every 30sec
            setTimeout('loadData()', refreshRate * 1000)
        }).fail( function(d, textStatus, error) {
            $('#status').text("getJSON failed, status: " + textStatus + ", error: "+error);
            // retry after 60sec
            setTimeout('loadData()', 60000)
        });;
    }
}

function Timespan(name, multiplier) {
    this.name = name;
    this.multiplier = multiplier;
    this.calcEarnings = function(sum, rate) {
        return sum * Math.pow(1 + rate, multiplier) - sum;
    };
    this.formatEarnings = function(currency, earnings, minimize_currency_xs) {
        if (currency == "BTC" && this == Hour) {
            return printFloat(earnings * 100000000, 0) + " Satoshi / " + name + "<br/>";
        } else {
            var currencyClass = '';
            if (minimize_currency_xs) {
                currencyClass = 'hidden-xs';
            }
            if (currency == "BTC") {
                return displayUnit.formatValue(earnings) + " <span class=" + currencyClass + ">" + displayUnit.name + "</span> / " + name + "<br/>"
            } else if (currency == "USD" || currency == "USDT" || currency == "EUR") {
                return prettyFloat(earnings, 2) + " <span class=" + currencyClass + ">" + currency + "</span> / "+  name + "<br/>";
            } else {
                return printFloat(earnings, 8) + " <span class=" + currencyClass + ">" + currency + "</span> / "+  name + "<br/>";
            }
        }
    };
}

function BTCDisplayUnit(name, multiplier) {
    this.name = name;
    this.multiplier = multiplier;
    this.precision = Math.log10(multiplier);
    this.formatValue = function(value) {
        return printFloat(value * this.multiplier, 8 - this.precision);
    }
}

function setEffRateMode() {
    var q = location.search.match(/[\?&]effrate=[^&]+/);

    if (q) {
        //console.log('Got effective rate mode from URI');
        effRateMode = q[0].split('=')[1];
    } else {
        if (localStorage.effRateMode) {
            //console.log('Got effective rate mode from localStorage');
            effRateMode = localStorage.effRateMode;
        }
    }
    if (validEffRateModes.indexOf(effRateMode) == -1) {
        console.error(effRateMode + ' is not valid effective rate mode! Valid values are ' + validModes);
        effRateMode = validEffRateModes[0];
    }
    localStorage.effRateMode = effRateMode;
    $("input[name='effRateMode'][value='"+ effRateMode +"']").prop('checked', true);;
    console.log('Effective rate mode: ' + effRateMode);
}

function setBTCDisplayUnit() {
    var q = location.search.match(/[\?&]displayUnit=[^&]+/);
    var displayUnitText = 'BTC';

    if (q) {
        //console.log('Got displayUnitText from URI');
        displayUnitText = q[0].split('=')[1];
    } else {
        if (localStorage.displayUnitText) {
            //console.log('Got displayUnitText from localStorage');
            displayUnitText = localStorage.displayUnitText;
        }
    }

    $("input[name='btcDisplayUnit'][value='"+ displayUnitText +"']").prop('checked', true);;

    btcDisplayUnitsModes.forEach(function(unit) {
        if(unit.name == displayUnitText) {
            displayUnit = unit;
            localStorage.displayUnitText = displayUnitText;
        }
    })
    console.log('displayUnitText: ' + displayUnitText);
}

function setOutputCurrencyDisplayMode() {
    var q = location.search.match(/[\?&]earningsInOutputCurrency=[^&]+/);
    var outputCurrencyDisplayModeText = 'all';

    if (q) {
        outputCurrencyDisplayModeText = q[0].split('=')[1];
    } else {
        if (localStorage.outputCurrencyDisplayModeText) {
            outputCurrencyDisplayModeText = localStorage.outputCurrencyDisplayModeText;
        }
    }

    $("input[name='outputCurrencyDisplayMode'][value='"+ outputCurrencyDisplayModeText +"']").prop('checked', true);;

    validOutputCurrencyDisplayModes.forEach(function(mode) {
        if(mode == outputCurrencyDisplayModeText) {
            outputCurrencyDisplayMode = mode;
            localStorage.outputCurrencyDisplayModeText = outputCurrencyDisplayModeText;
        }
    })
    console.log('outputCurrencyDisplayMode: ' + outputCurrencyDisplayModeText);

}

function loadSettings() {
    // Refresh rate
    refreshRate = localStorage.getItem('refreshRate') || 30
    $('#refresh_interval').val(refreshRate)

    // Time spans
    var timespanNames = JSON.parse(localStorage.getItem('timespanNames')) || ["Year", "Month", "Week", "Day", "Hour"]

    timespans = [Year, Month, Week, Day, Hour].filter(function(t) {
        // filters out timespans not specified
        return timespanNames.indexOf(t.name) !== -1;
    });

    timespanNames.forEach(function(t) {
        $('input[data-timespan="' + t + '"]').prop('checked', true);
    });
}

function doSave() {
    // Validation
    var tempRefreshRate = $('#refresh_interval').val()
    if(tempRefreshRate < 10 || tempRefreshRate > 60) {
        alert('Please input a value between 10 and 60 for refresh rate')
        return false
    }

    // Refresh rate
    localStorage.setItem('refreshRate', tempRefreshRate)

    // Time spans
    var timespanNames = [];
    $('input[type="checkbox"]:checked').each(function(i, c){
        timespanNames.push($(c).attr('data-timespan'));
    });
    localStorage.setItem('timespanNames', JSON.stringify(timespanNames))

    // Bitcoin Display Unit
    localStorage.displayUnitText = $('input[name="btcDisplayUnit"]:checked').val();
    btcDisplayUnitsModes.forEach(function(unit) {
        if(unit.name == localStorage.displayUnitText) {
            displayUnit = unit;
        }
    })

    // OutputCurrencyDisplayMode
    localStorage.outputCurrencyDisplayModeText = $('input[name="outputCurrencyDisplayMode"]:checked').val();
    if(validOutputCurrencyDisplayModes.indexOf(localStorage.outputCurrencyDisplayModeText) !== -1) {
        outputCurrencyDisplayMode = localStorage.outputCurrencyDisplayModeText;
    }

    //Effective rate calculation
    localStorage.effRateMode = $('input[name="effRateMode"]:checked').val();
    if(validEffRateModes.indexOf(localStorage.effRateMode) !== -1) {
        effRateMode = localStorage.effRateMode;
    }

    toastr.success("Settings saved!");
    $('#settings_modal').modal('hide');

    // Now we actually *use* these settings!
    update();
}

function update() {
    loadSettings();
    setEffRateMode();
    setBTCDisplayUnit();
    setOutputCurrencyDisplayMode();
    loadData();
    if (window.location.protocol == "file:") {
        $('#file').show();
    }
}

// https://github.com/twbs/bootstrap/issues/14040#issuecomment-253840676
function bsNavbarBugWorkaround() {
    var nb = $('nav.navbar-fixed-top');
    $('.modal').on('show.bs.modal', function () {
        nb.width(nb.width());
    }).on('hidden.bs.modal', function () {
        nb.width(nb.width('auto'));
    });
}

$(document).ready(function () {
    toastr.options = {
        "positionClass": "toast-top-center"
    }

    update();
    bsNavbarBugWorkaround();
});
