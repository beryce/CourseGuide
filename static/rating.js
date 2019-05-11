/* global $ */
var progressive_on = false;
$("#progressive_enhancement").on('click', function () {
    if(progressive_on) {
        // turn it off
        $("input[name=stars],input[type=submit]").show();
        $("#progressive_enhancement").text('Turn on Progressive Enhancement');
        progressive_on = false;
    } else {
        // turn it on
        $("input[name=stars],input[type=submit]").hide();
        $("#progressive_enhancement").text('Turn off Progressive Enhancement');
        progressive_on = true;
    }
});

