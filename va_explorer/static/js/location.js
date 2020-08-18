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

  $(".location-select").on('select2:select', function(e) {
    const data = e.params.data;
    let descendants = data.element.dataset.descendants;
    let locationsToDisableHash = descendantsHash(descendants);

    toggleLocationState(locationsToDisableHash, true);
  });

  $(".location-select").on('select2:unselect', function(e) {
    const data = e.params.data;
    let descendants = data.element.dataset.descendants;
    let locationsToEnableHash = descendantsHash(descendants);

    toggleLocationState(locationsToEnableHash, false)
  });

  function descendantsHash(descendants) {
    let descendantsHash = {};
    if(descendants!=='') {
      descendants = descendants.replace(/'/g, '"');

      JSON.parse(descendants).forEach(function(element) {
        descendantsHash[element] = true;
      });
    }
    return descendantsHash;
  }

  function toggleLocationState(locationsHash, disabledState) {
    $(".location-select option").filter(function() {
      return this.value in locationsHash;
    }).prop('disabled', disabledState);
  }
});
