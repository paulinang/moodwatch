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
function createMoodChart(minDate, maxDate, options) {
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
function changeTimeWindow(timeWindow) {
    if (timeWindow == 'monthly') {
        // enable time nav button
        // debugger;
        $('.move-time-button').attr('disabled', false);
        $.get('/mood_chart.json',
            {minDate: moment().startOf('month').format('YYYY-MM-DD'),
             maxDate: moment().endOf('month').format('YYYY-MM-DD')},
             function (data) {
                debugger;
                moodChart.data = data;
                moodChart.options.scales.xAxes[0].time.min = moment().startOf('month').format('YYYY-MM-DD');
                moodChart.options.scales.xAxes[0].time.max = moment().endOf('month').format('YYYY-MM-DD');
                moodChart.update();
             })        
    }
    // else if (timeWindow == 'all-time') {
    //     // disable time nav button
    //     $('.move-time-button').attr('disabled', true);
    //     // change xAxes min/max to earliest log/ current day
    //     moodChart.options.scales.xAxes[0].time.min = minDate;
    //     moodChart.options.scales.xAxes[0].time.max = moment().format('YYYY-MM-DD');
    //     moodChart.update();
    // }
}

// Moves chart in time based on user clicking back/forth buttons
$('.move-time-button').on('click', function () {
            var timeWindow = ($('#chart-time-window').val());
            if (this.value == 'backward') {
                moodChart.options.scales.xAxes[0].time.min.subtract(1, 'month');
                moodChart.options.scales.xAxes[0].time.max.subtract(1, 'month');
                moodChart.update();
            }
            else if ((this.value == 'forward') && (moodChart.options.scales.xAxes[0].time.max < moment().endOf('month'))) {
                moodChart.options.scales.xAxes[0].time.min.add(1, 'month');
                moodChart.options.scales.xAxes[0].time.max.add(1, 'month');
                moodChart.update();
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
