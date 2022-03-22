/* Enable Boostrap tooltips */
$(function () {
  $('[data-toggle="tooltip"]').tooltip({
    trigger : 'hover'
  })
})
$('#hidden-check').change(function() {
  $('tr[data-value="nan"]').toggle();
  $('tr[data-value=""]').toggle();
})
$('tr[data-value="nan"]').css('display', "none");
$('tr[data-value=""]').css('display',"none");