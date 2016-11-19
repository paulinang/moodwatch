// Set options for chart.js mood chart
function initializeOptions(minDate, maxDate) {
    var options = { responsive: true,
                maintainAspectRatio: false,
                // http://stackoverflow.com/questions/37061945/how-to-format-x-axis-time-scale-values-in-chart-js-v2
                scales: {
                    xAxes: [{
                        type:'time',
                        unit: 'day',
                        unitStepSize: 1,
                        time: {
                            displayFormats: {
                                'day': 'MMM DD'
                            },
                            max: maxDate,
                            min: minDate,
                        } 
                    }],
                    yAxes: [{
                        // set y axis min and max from -50 to 50
                        ticks: {
                            min: -50,
                            max: 50
                        }
                    }]
                },
                legend: {
                    // hide label for each dataset
                    display: false
                }};
    return options
}

// AJAX request for json to create line chart with
function createMoodChart(minDate, maxDate) {
    var options = initializeOptions(minDate, maxDate);
    $.get('/mood_chart.json',
        {minDate: minDate,
         maxDate: maxDate},
         function (data) {
            moodChart = new Chart(ctx, {
                type: 'line',
                data: data,
                options: options
            });
        });
}

// Changes time window according to user selection in dropdown menu
var timeWindows = {'month': 1,
                   'quarter': 3,
                   'bi-annual': 6,
                   'year': 12};


function changeTimeWindow(timeWindow) {
    moodChart.destroy();
    $('.move-time-button').attr('disabled', false);
    if (timeWindow == 'bi-annual') {
        if (moment().month() < 6) {
            var minDate = moment().startOf('year').format('YYYY-MM-DD');
            var maxDate = moment().set({'month': 5, 'date': 30}).format('YYYY-MM-DD');
        }
        else {
            var minDate = moment().set({'month': 6, 'date': 1}).format('YYYY-MM-DD');
            var maxDate = moment().endOf('year').format('YYYY-MM-DD');
        }
    }
    else if (timeWindow == 'all-time') {
        // disable time nav button
        $('.move-time-button').attr('disabled', true);
        // change xAxes min/max to earliest log/ current day
        var minDate = firstLog;
        var maxDate = moment().format('YYYY-MM-DD');
    }
    else {
        var minDate = moment().startOf(timeWindow).format('YYYY-MM-DD');
        var maxDate = moment().endOf(timeWindow).format('YYYY-MM-DD');
    }
    createMoodChart(minDate, maxDate);
}

// Moves chart in time based on user clicking back/forth buttons
$('.move-time-button').on('click', function () {
            var timeWindow = ($('#chart-time-window').val());
            var currentMinDate = moment(moodChart.options.scales.xAxes[0].time.min);
            var currentMaxDate = moment(moodChart.options.scales.xAxes[0].time.max);
            // to compare absolute max date with currentMax Date
            // must specify startOf('day') as endOf(period) also sets it to end of day
            var absMaxDate = moment().endOf(timeWindow).startOf('day');

            // moment.js does not recognize 'bi-annual' like 'quarter' or 'year'
            // have to set my own 'endOf' 'bi-annual' for 1st and 2nd half of year
            if (timeWindow == 'bi-annual'){
                absMaxDate = moment().endOf('year').startOf('day');
                if (moment().month() < 6){
                    absMaxDate = moment().set({'month': 5, 'date': 30});
                }
            }

            if ((this.value == 'forward') && (currentMaxDate.isBefore(absMaxDate))) {
                // debugger;
                var newMinDate = currentMinDate.add(timeWindows[timeWindow], 'month').format('YYYY-MM-DD');
                var newMaxDate = currentMaxDate.add(timeWindows[timeWindow], 'month').format('YYYY-MM-DD');
                moodChart.destroy();
                createMoodChart(newMinDate, newMaxDate);                
            }

            if ((this.value == 'backward') && (currentMaxDate.isSameOrBefore(absMaxDate))) {
                var newMinDate = currentMinDate.subtract(timeWindows[timeWindow], 'month').format('YYYY-MM-DD');
                var newMaxDate = currentMaxDate.subtract(timeWindows[timeWindow], 'month').format('YYYY-MM-DD');
                moodChart.destroy();
                createMoodChart(newMinDate, newMaxDate);               
            }
        });

// $('#toggle-events').on('click', function () {
//     var events = moodChart.data.datasets.filter(function (dataset) {return dataset.label == 'event'});
//     console.log(events);
//     for (i=0; i<events.length; i++) {
//         if (events[i].borderColor != 'rgba(255,153,0,0.4)') {
//             events[i].borderColor = 'rgba(255,153,0,0.4)';
//         }
//         else {
//             events[i].borderColor = 'rgba(0,0,0,0)';
//         }
//     }
//     moodChart.update();

// });


        



        // $('#toggle-events').on('click', function () {
        //     var events = moodChart.data.datasets.filter(function (dataset) {return dataset.label == 'event'});
        //     console.log(events);
        //     for (i=0; i<events.length; i++) {
        //         if (events[i].borderColor != 'rgba(255,153,0,0.4)') {
        //             events[i].borderColor = 'rgba(255,153,0,0.4)';
        //         }
        //         else {
        //             events[i].borderColor = 'rgba(0,0,0,0)';
        //         }
        //     }
        //     moodChart.update();

        // });
