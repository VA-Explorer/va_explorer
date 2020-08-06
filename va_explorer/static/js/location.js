$(document).ready(function() {
  function formatResult(node) {
  var level = 0;
  var text_transform = 'capitalize';
  var font_weight = 'normal';
  var font_style = 'normal';

  if(node.element !== undefined){
    level = (node.element.className);
    if(level.trim() !== ''){
      level = (parseInt(level.match(/\d+/)[0]))-1;
    }
    if(level===0) {
      text_transform = 'uppercase';
    }
    else if(level===2) {
      font_style = 'italic';
    }
  }
  const left_padding = (20 * level);

  return $('<span style="padding-left:' + left_padding + 'px; text-transform:' + text_transform + '; ' +
      'font-weight:' + font_weight + '; ' + 'font-style:' + font_style + ';">' + node.text + '</span>');
  }

  $(".js-example-basic-single").select2({
    placeholder: "Search for location(s) to add to user's geographic access",
    templateResult: formatResult,
  });
});
