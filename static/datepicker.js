function createDatepicker(datepickerId) {
    $(datepickerId).datepicker({            
        minDate: '-1M',
        maxDate: new Date(),
        dateFormat: 'yy-mm-dd',
        // beforeShowDay takes a date from the calendar and returns an array
        // returns [t/f slectable, css class name to add '' if none, optional popup tooltip]
    });
}

function excludeLoggedDays(datepickerId, excludeDates) {
    $(datepickerId).datepicker('option', 'beforeShowDay', function(date) {
            // turn date from datepicker into a str
            var dateStr = $.datepicker.formatDate('yy-mm-dd', date);
            // return whether dateStr is in excludeDates
            // array.indexOf(item) returns -1 if item not in array
            return [excludeDates.indexOf(dateStr) == -1]
    });
}

function validateMoodRange(evt){
            var overallMood = $('#overall-mood').val()
            var minMood = $('#min-mood').val()
            var maxMood = $('#max-mood').val()

            if ((minMood && maxMood)) {
                // .val() returns str, need to make it int for comparisons
                overallMood = parseInt(overallMood)
                minMood = parseInt(minMood)
                maxMood = parseInt(maxMood)

                if (minMood > maxMood) {
                    var msg = '** Min should not be greater than max **'
                    // evt.preventDefault();
                    // $('#alert-msg').html('** Min should not be greater than max **');
                }
                else if (!((minMood < overallMood) && (overallMood < maxMood))) {
                    var msg = '** Overall mood should be within mood range **'
                    // evt.preventDefault();
                    // $('#alert-msg').html('** Overall mood should be within mood range **');
                }
            }
            else if ((!minMood && maxMood) || (!maxMood && minMood)) {
                var msg = '** Both min and max must be entered or empty**';
            }

            if (msg) {
                evt.preventDefault();
                $('#alert-msg').html(msg);
            }
        }