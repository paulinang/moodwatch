//////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////                                            ////////////////////////////////////
//////////////////////////////////            FX FOR USING CHART.JS           ////////////////////////////////////
//////////////////////////////////                                            ////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// SETS OPTIONS FOR THE CHART IN CHART.JS
function initializeOptions(minDate, maxDate) {
    var options = { responsive: true,
                    maintainAspectRatio: false,
                    // http://stackoverflow.com/questions/37061945/how-to-format-x-axis-time-scale-values-in-chart-js-v2
                    scales: {
                        xAxes: [{
                            type:'time',
                            unit: 'day',
                            unitStepSize: 0,
                            time: {
                                displayFormats: {
                                    'day': 'MMM DD'
                                },
                                max: maxDate,
                                min: minDate,
                            },
                            ticks: {
                                fontColor: 'rgba(0,0,0,.7)',
                                // fontStyle: 'bold',
                                fontSize: 14}
                        }],
                        yAxes: [{
                            // set y axis min and max from -50 to 50
                            ticks: {
                                fontColor: 'rgba(0,0,0,.7)',
                                fontStyle: 'bold',
                                fontSize: 14,
                                min: -50,
                                max: 50
                            }
                        }]
                    },
                    legend: {
                        // hide label in legend for each dataset
                        display: false
                    }
                };
    return options
}


////////////////////////////////////////////////////////////////////
///////////           CREATE CHART FUNCTIONS           /////////////
////////////////////////////////////////////////////////////////////

// CREATE A CHART OF MOOD LOGS OVER MULTIPLE DATES
function createMoodChart(minDate, maxDate) {
    var options = initializeOptions(minDate, maxDate);

    // AJAX get request for mood chart data
    $.get('/mood_chart.json',
        {minDate: minDate,
         maxDate: maxDate},
         function (data) {
            // Create a linechart with retrieved data
            moodChart = new Chart(ctx, {
                type: 'line',
                data: data,
                options: options
            });
            $('.mood-chart').css('visibility', 'visible');
        });

}


// CREATE HIGH LEVEL MOOD CHART OF CLIENT FOR PRO USER
function createClientChart(minDate, maxDate, clientId) {
    var options = initializeOptions(minDate, maxDate);
    //AJAX get request for specfic client's 'smooth' mood data
    $.get('/client_log_overview.json',
        {clientId: clientId},
         function (data) {
            options.scales.xAxes[0].time.min = data['min_date'];
            moodChart = new Chart(ctx, {
                type: 'line',
                data: {'datasets': data.datasets},
                options: options
            });
        });
}


// CREATE CHART FOR SPECIFIC DAY
function createDayChart(day) {
    $('#today-date-str').html(day);
    var minDate = moment(day).subtract(1, 'day').format('YYYY-MM-DD');
    var maxDate = moment(day).add(1, 'day').format('YYYY-MM-DD');
    var options = initializeOptions(minDate, maxDate);
    // Set xAxes labels to not show
    // (hide ugle time labels since chart only for one day)
    options.scales.xAxes[0].display = false;
    options.scales.yAxes[0].ticks.fixedStepSize = 10;
    // options.title.text = 'Logs for ' + day;
    // AJAX get request for specific day data
    $.get('/day_chart.json',
        {day: day},
         function (data) {
            dayChart = new Chart(dCtx, {
                type: 'line',
                data: data,
                options: options
            });
            $('#day-chart').css('visibility', 'visible');
        });
}


////////////////////////////////////////////////////////////////////
///////////          INTERACTIVE FEATURES FXS          /////////////
////////////////////////////////////////////////////////////////////

// CHANGE TIME WINDOW OF MOOD CHART
// Changes according to user selection of dropdown options
// Will adjust to time window containing current day
function changeTimeWindow(timeWindow) {
    $('.mood-chart').css('visibility', 'hidden');
    moodChart.destroy();

    // if all logs requested, set min to first log and max to current day
    if (timeWindow == 'all-time') {
        // disable time nav button
        $('.move-time-button').attr('disabled', true);
        // change xAxes min/max to earliest log/ current day
        var minDate = firstLog;
        var maxDate = moment().format('YYYY-MM-DD');
    }
    else if (timeWindow == 'bi-annual') {
        // enable time nav button
        $('.move-time-button').attr('disabled', false);

        // bi-annual is not a native time window for moment.js
        // if current month is in the first half
        if (moment().month() < 6) {
            // set min to start of year, max to end of june
            var minDate = moment().startOf('year').format('YYYY-MM-DD');
            var maxDate = moment().set({'month': 5, 'date': 30}).format('YYYY-MM-DD');
        }
        else {
            // if in second half, set min to start of july, max is end of year
            var minDate = moment().set({'month': 6, 'date': 1}).format('YYYY-MM-DD');
            var maxDate = moment().endOf('year').format('YYYY-MM-DD');
        }
    }
    else {
        $('.move-time-button').attr('disabled', false);
        // all other time windows are recognized by moment.js
        var minDate = moment().startOf(timeWindow).format('YYYY-MM-DD');
        var maxDate = moment().endOf(timeWindow).format('YYYY-MM-DD');
    }
    createMoodChart(minDate, maxDate);
    changeTimeWindowStr(timeWindow, minDate, maxDate);
}


// MOVE BACK/FORTH IN TIME
// 'Step' is time window selected
var timeWindowMonths = {'month': 1,
                   'quarter': 3,
                   'bi-annual': 6,
                   'year': 12};

$('.move-time-button').on('click', function () {
            // Gets current time window selected
            var timeWindow = ($('#chart-time-window').val());
            var step = timeWindowMonths[timeWindow];

            // Gets current max and min of the xAxes to know what to step back/forward from
            var currentMinDate = moment(moodChart.options.scales.xAxes[0].time.min);
            var currentMaxDate = moment(moodChart.options.scales.xAxes[0].time.max);

            // Get absolute max date to compare with
            var absMaxDate = moment().endOf(timeWindow).startOf('day');
            // must specify startOf('day') as endOf(period) also sets it to end of day
            // deals with 'bi-annual' not recognized by moment.js
            if (timeWindow == 'bi-annual'){
                absMaxDate = moment().endOf('year').startOf('day');
                if (moment().month() < 6){
                    absMaxDate = moment().set({'month': 5, 'date': 30});
                }
            }

            // If user requests going forward
            // Only allow if time window currently viewed is earlier than time window containing current day
            if ((this.value == 'forward') && (currentMaxDate.isBefore(absMaxDate))) {
                console.log(currentMaxDate);
                console.log(absMaxDate);
                // when creating new min and max dates, explicitly ask for start and end of month
                // deals with problem of being able to go forward one time window past abs maxdate
                var newMinDate = currentMinDate.add(step, 'month').startOf('month').format('YYYY-MM-DD');
                var newMaxDate = currentMaxDate.add(step, 'month').endOf('month').format('YYYY-MM-DD');
                $('.mood-chart').css('visibility', 'hidden');
                moodChart.destroy();
                createMoodChart(newMinDate, newMaxDate);
                changeTimeWindowStr(timeWindow, newMinDate, newMaxDate);
            }
            // If user requests going backward
            if ((this.value == 'backward')) {              
                var newMinDate = currentMinDate.subtract(step, 'month').startOf('month').format('YYYY-MM-DD');
                var newMaxDate = currentMaxDate.subtract(step, 'month').endOf('month').format('YYYY-MM-DD');
                $('.mood-chart').css('visibility', 'hidden');
                moodChart.destroy();
                createMoodChart(newMinDate, newMaxDate);
                changeTimeWindowStr(timeWindow, newMinDate, newMaxDate);       
            }
        });


// TOGGLE EVENT VISIBILITY
function toggleEvents() {
    // Get datasets that are events
    var events = moodChart.data.datasets.filter(function (dataset) {
            return dataset.label == 'event';
        });
        for (i=0; i<events.length; i++) {
            // Show event if previously invisible
            if (events[i].backgroundColor != 'rgba(255,153,0,1)') {
                events[i].backgroundColor = 'rgba(255,153,0,1)';
                $('#toggle-events').css('background-color', 'rgba(255,153,0,0.6)');
            }
            else {
                events[i].backgroundColor = 'rgba(0,0,0,0)';
                $('#toggle-events').css('background-color', 'rgba(255,255,255,1)');
            }
        }
    moodChart.update();
}


// TOGGLE MOOD ANALYSIS VISIBILITY
function toggleAnalysis(analysisType){
    var colorRef = {'roll-avg': 'rgba(101,19,10',
                    'roll-std': 'rgba(26,81,63'};
    var analysis = moodChart.data.datasets.filter(function (dataset) {
        return dataset.label == analysisType;
    });
    if (analysis[0].borderColor != (colorRef[analysisType] + ',1)')) {
        analysis[0].borderColor = (colorRef[analysisType] + ',1)');
        $('#'+analysisType).css('background-color', (colorRef[analysisType] + ',.5)'));
    }
    else {
        analysis[0].borderColor = 'rgba(0,0,0,0)';
        $('#'+analysisType).css('background-color', 'rgba(255,255,255,1)');
    }
    moodChart.update();
}


// CHANGE TIME WINDOW TITLE STRING
function changeTimeWindowStr(timeWindow, minDate, maxDate) {
    var timeWindowStr;
    if (timeWindow == 'year') {
        timeWindowStr = 'Year ' + moment(minDate).format('YYYY');
    }
    else if (timeWindow == 'month') {
        timeWindowStr = moment(minDate).format('MMMM YYYY');
    }
    else if (timeWindow == 'all-time') {
        timeWindowStr = 'All Logs';
    }
    else {
        timeWindowStr = moment(minDate).format('MMMM YYYY') + ' to ' + moment(maxDate).format('MMMM YYYY');
    }
    $('#current-time-window').html(timeWindowStr);
};