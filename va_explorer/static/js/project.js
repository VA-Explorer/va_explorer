/* Enable Boostrap tooltips */
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})
$('#hidden-check').change(function() {
  var vis = this.checked ? 'visible' : 'hidden';
  var vis = this.checked ? 'none' : '';
  console.log("CONSOLEEEE");
  // $('.nan').css('visibility', vis);
  // $('td[class=""]').css('visibility',vis);
  $('.nan').css('display', vis);
  $('td[class=""]').css('display',vis);
})
$('.nan').css('display', "none");
$('td[class=""]').css('display',"none");