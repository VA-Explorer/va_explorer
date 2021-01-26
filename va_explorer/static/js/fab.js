$(document).ready(function () {
  /**
   * Simple toggle to show or hide a floating action button's menu items and
   * associated backdrop
   */
  $(".fab,.backdrop").click(function () {
    if ($(".backdrop").is(":visible")) {
      $(".backdrop").fadeOut(125);
      $(".fab.child")
        .stop()
        .animate({
          bottom: $("#main-fab").css("bottom"),
          opacity: 0
        }, 125, function () {
          $(this).hide();
        });
    } else {
      $(".backdrop").fadeIn(125);
      $(".fab.child").each(function () {
        $(this)
          .stop()
          .show()
          .animate({
            bottom: (parseInt($("#main-fab").css("bottom")) + parseInt($("#main-fab").outerHeight()) + 55 * $(this).data("subitem") - $(".fab.child").outerHeight()) + "px",
            opacity: 1
          }, 125);
      });
    }
  });

  // Start a scroll to top of page animation
  $('.fab.to-top').click(function () {
    $('html, body').animate({
      scrollTop: 0
    }, 1600);
    return false;
  });
  
  // Start a scroll to bottom of page animation
  $('.fab.to-bottom').click(function () {
    $('html, body').animate({
      scrollTop: document.body.scrollHeight
    }, 1600);
    return false;
  });
});