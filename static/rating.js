/* global $ */
/* global star_url */
/* star_url is defined in the search.html template. */

var uid = $("input[name=uid]").attr("value");
$("#courses-list").on('click','.favButton', function(event) {
    if(uid != 'False') {
        if(event.target != this) return;
        var cid = $(this).closest("[data-cid]").attr("data-cid");
        var favButton = $(this).closest("[data-cid="+cid+"]").find(".favButton");
        var favButtonText = $(this).closest("[data-cid="+cid+"]").find(".favButton").text();
        if(favButtonText == 'Star!') {
            // starred
            $.post(star_url, 
                {'cid': cid, 'isFav': 1},
                "json");
            favButton.text('Starred!');
        } else {
            // unstarred
            $.post(star_url, 
                {'cid': cid, 'isFav': 0},
                "json");
            favButton.text('Star!');
        }
    } else {
        console.log("user not logged in");
        $.post(star_url, 
                {'cid': '', 'isFav': ''},
                "json");
    }
});


