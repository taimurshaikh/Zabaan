// Ensures translate can not be pressed unless the input box has text in it
$(document).ready(function() {
    $('#input').on('input change', function() {
        if ($(this).val() == '') {
            $('#tongueBtn').prop('disabled', true);
            $('#saveChangesBtn').prop('disabled', true);
        } else {
            $('#tongueBtn').prop('disabled', false);
            $('#saveChangesBtn').prop('disabled', false);
        }
    });
    $('#editInput').on('input change', function() {
        if ($(this).val() == '') {
            $('#saveChangesBtn').prop('disabled', true);
        } else {
            $('#saveChangesBtn').prop('disabled', false);
        }

    });
    $('#editOutput').on('input change', function() {
        if ($(this).val() == '') {
            $('#saveChangesBtn').prop('disabled', true);
        } else {
            $('#saveChangesBtn').prop('disabled', false);
        }

    });

});




