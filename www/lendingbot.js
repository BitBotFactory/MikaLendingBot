var localFile, reader;

var Hour = new Timespan("Hour",1/24);
var Day = new Timespan("Day",1);
var Week = new Timespan("Week",7);
var Month = new Timespan("Month",30);
var timespans = [Month, Week, Day, Hour];

function updateJson(data) {
    $('#status').text(data.last_status);
    $('#updated').text(data.last_update);

    var rowCount = data.log.length;
    var table = $('#logtable');
    table.empty();
    for (var i = rowCount - 1; i >=0; i--) {
        table.append($('<tr/>').append($('<td colspan="2" />').text(data.log[i])));
    }

    updateRawValues(data.raw_data);
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
                if(!isNaN(highestBidBTC)) {
                    timespanEarningBTC = timespan.calcEarnings(lentSum * highestBidBTC, rate);
                    earningsBTC += timespan.formatEarnings("BTC", timespanEarningBTC);
                    totalBTCEarnings[timespan.name] += timespanEarningBTC;
                }
            });


            var effectiveRate = lentSum * rate * 100 / totalCoins;
            var yearlyRate = effectiveRate * 365; // no reinvestment
            var yearlyRateReinv = (Math.pow(effectiveRate / 100 + 1, 365) - 1) * 100; // with daily reinvestment
            var lentPerc = lentSum / totalCoins * 100;
            var poloRateText = '&nbsp;(<span title="Rate as seen on poloniex, before 15% fee.">poloniex</span>)';
            var effRateText =  '&nbsp;(<span title="Effective rate, after poloniex 15% fee.">effective</span>)';

            var rowValues = [currency,
                printFloat(lentSum, 4) + ' of ' + printFloat(totalCoins, 4) + ' (' + printFloat(lentPerc, 2) + '%)',
                printFloat(averageLendingRate, 5) + '% / Day' + poloRateText + '<br/>' + printFloat(effectiveRate, 5) +
                    '% / Day' + effRateText + '<br/>' + printFloat(yearlyRate, 2) + '% / Year (not reinvest)<br/>' +
                    printFloat(yearlyRateReinv, 2) + '% / Year (reinvest)' ];

            // print coin status
            var row = table.insertRow();
            for (var i = 0; i < rowValues.length; ++i) {
                var cell = row.appendChild(document.createElement("td"));
                cell.innerHTML = rowValues[i];
            }

            var earningsColspan = rowValues.length - 1;
            // print coin earnings
            var row = table.insertRow();
			if(lentSum > 0) {
				var cell = row.appendChild(document.createElement("td"));
				cell.innerHTML = "<b>"+ currency +"<br/>Estimated<br/>Earnings<b>";
				cell = row.appendChild(document.createElement("td"));
				cell.setAttribute("colspan", earningsColspan);
				if(!isNaN(highestBidBTC))
					cell.innerHTML = earnings + "<br/>"+ couple +" highest bid: "+ printFloat(highestBidBTC, 8) + "<br/>" + earningsBTC;
				else
					cell.innerHTML = earnings;
			}
        }
    }

    // add headers
    var thead = table.createTHead();
    var row = thead.insertRow();
    var rowValues = ["Coin", "Active Loans", "Average Loan<br/>Interest Rate"];
    for (var i = 0; i < rowValues.length; ++i) {
        var cell = row.appendChild(document.createElement("th"));
        cell.innerHTML = rowValues[i];
    }

    // show account summary
    if(currencies.length > 1) {
        earnings = '';
        timespans.forEach(function(timespan) {
            earnings += timespan.formatEarnings( 'BTC', totalBTCEarnings[timespan.name]);
        });
        var row = thead.insertRow(0);
        var cell = row.appendChild(document.createElement("th"));
        cell.innerHTML = "Account<br/>Estimated<br/>Earnings";
        cell.style.verticalAlign = "text-top";
        cell = row.appendChild(document.createElement("th"));
        cell.setAttribute("colspan", rowValues.length - 1);
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
            return printFloat(earnings * 100000000, 0) + " Satoshi / Hour<br/>";
        } else {
            return printFloat(earnings, 8) + " " + currency + " / " + name + "<br/>";
        }
    };
}

$(document).ready(function () {
    loadData();
    if(window.location.protocol == "file:") {
        $('#file').show();
    }
});
