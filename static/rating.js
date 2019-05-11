/* global $ */

var editPostUrl = "{{url_for('editPostAjax')}}"
$("#past-posts").on("click", ".edit-post-button", function(event) {
    console.log("BUTTON CLICKED")
    var post = $(this).closest("tr");
    var postId = $(this).closest("[post-pid]").attr("post-pid");
    var courseId = $(this).closest("[post-pid]").find(".course_id").text();
    var courseName = $(this).closest("[post-pid]").find(".course_name").text();
    var rating = $(this).closest("[post-pid]").find(".rating").text();
    var hrs = $(this).closest("[post-pid]").find(".hours").text();
    var comments = $(this).closest("[post-pid]").find(".comments").text();
    console.log("pid " + postId);
    console.log("cid " + courseId);
    console.log(courseName);
    console.log(rating);
    console.log(hrs);
    console.log(comments);
    $.post(editPostUrl, {'courseId': courseId});
    
});
