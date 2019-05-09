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

// past code for when we did ajax on rating course
// keeping this here for reference
// event handler for rating button
// $(".class-rating").on("click",
//     function(event) {
//         if (progressive_on) {
//             var rating = $('input[name=stars]:checked').val();
//             var cid = $(this).closest("input:hidden[name=cid]").val();
//             var hours = $(this).find('input[name=fname]').val();
//             var comment = $(this).find('textarea[name=comment]').val();
//             console.log("rating:" + rating);
//             console.log("cid: " + cid);
//             console.log("hours: " + hours);
//             console.log("comment: " + comment)
//             sendData({'rating': rating, 'hours': hours, 'cid': cid, 'comment': comment});
//         } else {
//             return;
//         }
            
//     });

// updates the ratings using response from Ajax
// function updateRatings(obj) {
//     console.log("Received response from back end.");
//     var avg_hours = obj.avg_hours;
//     var avg_rating = obj.avg_rating;
//     console.log("avg_hours: " + avg_hours);
//     console.log("avg_rating: " + avg_rating);
//     $("#rate-btn").closest("#avgrating").text(avg_rating);
//     $("#rate-btn").closest("#avghours").text(avg_hours);
// }

// // sends response using Ajax
// function sendData(data) {
//     console.log("Sending " + data + " to back end.");
//     $.get("/rateCourseAjax", data, updateRatings);
    
// }

