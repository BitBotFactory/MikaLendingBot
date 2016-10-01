var localFile, reader;

var Hour = new Timespan("Hour",1/24);
var Day = new Timespan("Day",1);
var Week = new Timespan("Week",7);
var Month = new Timespan("Month",30);
var timespans = [Month, Week, Day, Hour];
var Coin_Val = 1.00000000;
var Coin = "BTC";

function updateJson(data) {
    $('#status').text(data.last_status);
    $('#updated').text(data.last_update);

    var rowCount = data.log.length;
    var table = $('#logtable');
    table.empty();
    for (var i = rowCount - 1; i >=0; i--) {
        table.append($('<tr/>').append($('<td colspan="2" />').text(data.log[i])));
    }

    updateOutputCurrency(data.outputCurrency);
    updateRawValues(data.raw_data);
}

function updateOutputCurrency(outputCurrency){
	var OutCurr = Object.keys(outputCurrency);
	Coin = outputCurrency['currency'];
	if(Coin != "BTC") {
		Coin_Val = parseFloat(outputCurrency['highestBid']);
	}	
}

function updateRawValues(rawData){
    var table = document.getElementById("detailsTable");
    table.innerHTML = "";
    var currencies = Object.keys(rawData);
    var totalBTCEarnings = {};
    for (var keyIndex = 0; keyIndex < currencies.length; ++keyIndex)
    {
        var currency = currencies[keyIndex];
        var averageLendingRate = parseFloat(rawData[currency]['averageLendingRate']);
        var lentSum = parseFloat(rawData[currency]['lentSum']);
        var totalCoins = parseFloat(rawData[currency]['totalCoins']);
        var highestBidBTC = parseFloat(rawData[currency]['highestBid']);
        var couple = rawData[currency]['couple'];

        if(!isNaN(averageLendingRate) && !isNaN(lentSum) || !isNaN(totalCoins))
        {

            // cover cases where totalCoins isn't updated because all coins are lent
            if(isNaN(totalCoins) && !isNaN(lentSum)) {
                totalCoins = lentSum;
            }
            var rate = +averageLendingRate  * 0.85 / 100; // 15% goes to Poloniex fees

            var earnings = '';
            var earningsBTC = '';
            timespans.forEach(function(timespan) {
                // init totalBTCEarnings
                if(isNaN(totalBTCEarnings[timespan.name])) {
                    totalBTCEarnings[timespan.name] = 0;
                }

                // calculate coin earnings
                timespanEarning = timespan.calcEarnings(lentSum, rate);
                earnings += timespan.formatEarnings(currency, timespanEarning);
                if(currency == 'BTC') {
                    totalBTCEarnings[timespan.name] += timespanEarning;
                }

                // calculate BTC earnings
                if(!isNaN(highestBidBTC) && !(currency == 'BTC')) {
                    timespanEarningBTC = timespan.calcEarnings(lentSum * highestBidBTC, rate);
                    earningsBTC += timespan.formatEarnings("BTC", timespanEarningBTC);
                    totalBTCEarnings[timespan.name] += timespanEarningBTC;
                }
            });


            var effectiveRate = lentSum * rate * 100 / totalCoins;
            var yearlyRate = effectiveRate * 365; // no reinvestment
            var yearlyRateReinv = (Math.pow(effectiveRate / 100 + 1, 365) - 1) * 100; // with daily reinvestment
            var lentPerc = lentSum / totalCoins * 100;
            var avgRateText = '&nbsp;<span style="white-space:nowrap;" title="Average loan rate, simple average calculation of active loans rates.">Avg. (i)</span>';
            var effRateText =  '&nbsp;<span style="white-space:nowrap;" title="Effective loan rate, considering lent precentage and poloniex 15% fee.">Eff. (i)</span>';
            var compoundRateText =  '&nbsp;<span style="white-space:nowrap;" title="Compound yearly rate, the result of reinvesting the interest.">Comp. (i)</span>';

            var rowValues = ["<b>" + currency + "</b>",
                'Lent ' + printFloat(lentSum, 4) +' of ' + printFloat(totalCoins, 4) + ' (' + printFloat(lentPerc, 2) + '%)',
                "<div class='inlinediv' >" + printFloat(averageLendingRate, 5) + '% Day' + avgRateText + '<br/>'
                    + printFloat(effectiveRate, 5) + '% Day' + effRateText + '<br/></div>' 
                    + "<div class='inlinediv' >" + printFloat(yearlyRate, 2) + '% Year<br/>'
                    +  printFloat(yearlyRateReinv, 2) + '% Year' + compoundRateText + "</div>" ];

            // print coin status
            var row = table.insertRow();
            for (var i = 0; i < rowValues.length; ++i) {
                var cell = row.appendChild(document.createElement("td"));
                cell.innerHTML = rowValues[i];
                cell.style.verticalAlign = "text-top";
                if( i == 0) {
                    cell.setAttribute("width", "20%");
                }
            }

            var earningsColspan = rowValues.length - 1;
            // print coin earnings
            var row = table.insertRow();
            if(lentSum > 0) {
                var cell1 = row.appendChild(document.createElement("td"));
                cell1.innerHTML = "<span class='hidden-xs'>"+ currency +"<br/></span>Estimated<br/>Earnings";
                var cell2 = row.appendChild(document.createElement("td"));
                cell2.setAttribute("colspan", earningsColspan);
                if(!isNaN(highestBidBTC)) {
                    cell1.innerHTML += "<br/><span class='hidden-xs'><br/>" + couple +"</span> highest bid: "+ printFloat(highestBidBTC, 8);
                    cell2.innerHTML = "<div class='inlinediv' >" + earnings + "<br/></div><div class='inlinediv' style='padding-right:0px'>"+ earningsBTC + "</div>";
                } else {
                    cell2.innerHTML = "<div class='inlinediv' >" +earnings + "</div>";
                }
            }
        }
    }

    // add headers
    var thead = table.createTHead();

    // show account summary
    if(currencies.length > 1) {
        earnings = '';
        timespans.forEach(function(timespan) {
		if(Coin == "BTC") {
            		earnings += timespan.formatEarnings( Coin, totalBTCEarnings[timespan.name]);
		}
		if(Coin == "USDT") {
			earnings += timespan.formatEarnings( Coin, totalBTCEarnings[timespan.name]*Coin_Val);
		}
		if(Coin != "BTC" && Coin != "USDT") {
			earnings += timespan.formatEarnings( Coin, totalBTCEarnings[timespan.name]/Coin_Val);
		}
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
    if(localFile) {
        reader.readAsText(localFile, 'utf-8');
        setTimeout('loadData()',30000)
    } else {
        // expect the botlog.json to be in the same folder on the webserver
        var file = 'botlog.json';
        $.getJSON(file, function (data) {
            updateJson(data);
            // reload every 30sec
            setTimeout('loadData()',30000)
        }).fail( function(d, textStatus, error) {
           $('#status').text("getJSON failed, status: " + textStatus + ", error: "+error);
           // retry after 60sec
           setTimeout('loadData()',60000)
        });;
    }
}

function printFloat(value, precision) {
    var multiplier = Math.pow(10, precision);
    var result = Math.round(value * multiplier) / multiplier;
    return result = isNaN(result) ? "0" : result.toFixed(precision);
}

function Timespan(name, multiplier) {
    this.name = name;
    this.multiplier = multiplier;
    this.calcEarnings = function(sum, rate) {
        return sum * rate * this.multiplier;
    };
    this.formatEarnings = function(currency, earnings) {
        if(currency == "BTC" && this == Hour) {
            return printFloat(earnings * 100000000, 0) + " Satoshi / " + name + "<br/>";
        } else {
            var currencyClass = '';
            if(currency != "BTC" && currency != "USDT") {
                currencyClass = 'hidden-xs';
            }
	return printFloat(earnings, 8) + " <span class=" + currencyClass + ">" + currency + "</span> / "+  name + "<br/>";
	    
        }
    };
}

$(document).ready(function () {
    loadData();
    if(window.location.protocol == "file:") {
        $('#file').show();
    }
});
