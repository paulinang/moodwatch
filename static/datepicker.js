function validateMoodRange(evt){
    var overallMood = $(this).find('.overall-mood').val()
    var minMood = $(this).find('.min-mood').val()
    var maxMood = $(this).find('.max-mood').val()

    if ((minMood && maxMood)) {
        // .val() returns str, need to make it int for comparisons
        overallMood = parseInt(overallMood)
        minMood = parseInt(minMood)
        maxMood = parseInt(maxMood)

        if (minMood > maxMood) {
            var msg = '** Min should not be greater than max **'
            // evt.preventDefault();
            // $('.alert-msg').html('** Min should not be greater than max **');
        }
        else if (!((minMood < overallMood) && (overallMood < maxMood))) {
            var msg = '** Overall mood should be within mood range **'
            // evt.preventDefault();
            // $('.alert-msg').html('** Overall mood should be within mood range **');
        }
    }
    else if ((!minMood && maxMood) || (!maxMood && minMood)) {
        var msg = '** Both min and max must be entered or empty**';
    }

    if (msg) {
        evt.preventDefault();
        $('.alert-msg').html(msg);
    }
}