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