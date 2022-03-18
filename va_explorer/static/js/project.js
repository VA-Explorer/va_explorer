/* Enable Boostrap tooltips */
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})
$('#hidden-check').change(function() {
  var vis = this.checked ? 'none' : '';
  $('.nan').css('display', vis);
  $('td[class=""]').css('display',vis);
})
$('.nan').css('display', "none");
$('td[class=""]').css('display',"none");