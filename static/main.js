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
    $.get('/client_prescriptions.json', {client_id: clientId}, function(data) {
        $('.client-details').show()
        $('#client-name').html(data.username)
        var prescriptions = data.prescriptions
        var medText = ''
        for (var key in prescriptions) {
            // For each drug type in prescriptions add an unordered list element
            // Start an ordered list under that element
            medText = medText + '<li>' + key + '</li><ol>';
            var prescriptionArray = prescriptions[key];
            for (i = 0; i < prescriptionArray.length; i++) {
                // For each prescription of a drug, add it as an ordered list element
                var prescription = prescriptionArray[i];
                medText = medText + '<li>Started ' + prescription.start_date;
                // Label if it's active
                if (!prescription.end_date) {
                    medText = medText + ' [ACTIVE]';
                    if (prescription.pro_username == proUsername) {
                        medText = medText + '&nbsp;&nbsp;&nbsp;<button type="button" class="btn btn-primary btn-lg change-prescription-button" data-toggle="modal" data-target="#change-prescription-modal" data-prescription-id="' + prescription.prescription_id + '" data-drug-id="' + prescription.drug_id + '"">Change Prescription</button>';
                    }
                }
                medText = medText + '</li><ul>';

                if (prescription.end_date) {
                    medText = medText + '<li>Ended: ' + prescription.end_date;
                }
                medText = medText + '<li>Prescribed by: ' + prescription.pro_username;
                medText = medText + '</li><li>Instructions: ' + prescription.instructions;
                if (prescription.notes) {
                    medText = medText + '</li><li>Notes: ' + prescription.notes;
                }
                medText = medText + '</li></ul>'
            }
        medText = medText + '</li></ol>'
        
        }
        medText = medText + '</ul>';
        $('#client-meds').html(medText);
    });
    if (moodChart) {
        moodChart.destroy();
    }

    var currentYear = [
        moment().startOf('year').format('YYYY-MM-DD'),
        moment().endOf('year').format('YYYY-MM-DD')
        ];
    createClientChart(currentYear[0], currentYear[1], clientId);
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
