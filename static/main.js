// VALIDATE MOOD RANGE BEFORE SUBMISSION OF LOG
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


// GET LOGS FOR A DAY
function displaySearchResults(requestedDay) {
    // Empty log details if previously populated
    $('.main-log').empty();
    $('.associated-logs').empty();

    // Show log detail div if previously hidden
    $('.log-details').show();

    // Populate log detail div with search results
    $.get('/logs_html.json', {searchDate: requestedDay}, function(data) {
        if (data) {
            $('.main-log').html(data.day_html);

            if (data.event_html) {
                $('.associated-logs').html(data.event_html);
            }
        }
        else {
            $('.main-log').html('<h4>There are no logs for this day</h4>');
        }
    });
}


/// GET CLIENT DATA
 function showClientData(clientId, proUsername) {
    $.get('/client_active_meds.json', {clientId: clientId}, function(data) {
        $('.client-info').show();
        // $('#client-name').html(data.username);
        var activeMeds = data.active_meds;
        $('#client-active-meds').html(activeMeds);
    });
    if (moodChart) {
        moodChart.destroy();
    }

    var minDate = moment().subtract(30, 'days').format('YYYY-MM-DD');
    var maxDate = moment().format('YYYY-MM-DD');
    createClientChart(minDate, maxDate, clientId);
}


// END PRESCRIPTION
function endPrescription(prescriptionId) {
    $.post('/end_prescription.json',
        {prescriptionId: prescriptionId, currentDate: $('#start-date').val()},
        function(data) {});
}

//ADD PRESCRIPTION
function addPrescription() {
    $.post('/add_prescription.json', formInputs, function(data) {
        $('#change-prescription-modal').modal('hide');
    });
}

//SHOW ALL PRESCRIPTIONS FOR DRUG
function showPrescriptions(clientId, drugId) {
    $('.table').show();
    var medTable = $('#client-prescriptions-for-drug');
    medTable.empty();
    $.get('/client_prescriptions_for_drug.json',
        {clientId: clientId, drugId: drugId},
        function(data){
            medTable.html(data.meds_html);
        });
}
