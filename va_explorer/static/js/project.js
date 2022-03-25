/* Enable Boostrap tooltips */
$(function () {
  $('[data-toggle="tooltip"]').tooltip({
    trigger : 'hover'
  })
})
$('#hidden-missing').change(function() {
  $('tr[data-value="N/A"]').toggle();
  $('tr[data-value=""]').toggle();
})
$('#hidden-redacted').change(function() {
  $('tr[data-value="** redacted **"]').toggle();
})
$('tr[data-value="N/A"]').css('display', "none");
$('tr[data-value=""]').css('display',"none");
