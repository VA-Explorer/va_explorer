$(document).ready(function () {
  /**
   * Simple toggle to show or hide a floating action button's menu items and
   * associated flt-action-backdrop
   */
  $(".flt-action-btn,.flt-action-backdrop").click(function () {
    if ($(".flt-action-backdrop").is(":visible")) {
      $(".flt-action-backdrop").fadeOut(125);
      $(".flt-action-btn.child")
        .stop()
        .animate({
          bottom: $("#main-fab").css("bottom"),
          opacity: 0
        }, 125, function () {
          $(this).hide();
        });
    } else {
      $(".flt-action-backdrop").fadeIn(125);
      $(".flt-action-btn.child").each(function () {
        $(this)
          .stop()
          .show()
          .animate({
            bottom: (parseInt($("#main-fab").css("bottom")) + parseInt($("#main-fab").outerHeight()) + 55 * $(this).data("subitem") - $(".flt-action-btn.child").outerHeight()) + "px",
            opacity: 1
          }, 125);
      });
    }
  });

  // Start a scroll to top of page animation
  $('.flt-action-btn.to-top').click(function () {
    $('html, body').animate({
      scrollTop: 0
    }, 1600);
    return false;
  });
  
  // Start a scroll to bottom of page animation
  $('.flt-action-btn.to-bottom').click(function () {
    $('html, body').animate({
      scrollTop: document.body.scrollHeight
    }, 1600);
    return false;
  });
});
