$(document).ready(function() {
  function formatResult(node) {
    let depth = 0;

    if(node.element !== undefined){
      depth = node.element.getAttribute('data-depth');

      if(depth.trim() !== ''){
        depth = parseInt(depth.match(/\d+/)[0]);
      }
    }

    return $('<span class="location-tree-depth-'+depth+'">'+ node.text +'</span>');
  }

  $(".location-select").select2({
    placeholder: "Search for location(s) to add to user's geographic access",
    templateResult: formatResult,
  });

  $(".location-select").on('change', function (e) {
    console.log($('select option:selected').attributes);
    $('select option:selected').prop('disabled', true);
  });

  $(".location-select").on('select2:unselect', function (e) {
    console.log("Called!")
    $('select option:not(:selected)').prop('disabled', false);
  });
});
