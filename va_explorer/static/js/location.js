  /**
   * Summary. Governs the behavior of the select2 Locations dropdown
   *
   * Examples: User creation and update forms.
   *
   * Note: CSS styling is used to emulate hierarchy due to HTML specification
   * which allows only one level of nesting in optgroup
   * https://select2.org/options#hierarchical-options
   */

$(document).ready(function() {
  /**
   * Summary. Initializes the select2 dropdown
   *
   */
  $(".location-select").select2({
    placeholder: "Search for location(s) to add to user's geographic access",
    templateResult: formatResult,
  });

  /**
   * Summary. Disables the descendant locations, if any, of a location that is selected
   *          Removes any previously-selected descendant locations from the select2 input field
   */
  $(".location-select").on('select2:select', function(e) {
    let descendants = e.params.data.element.dataset.descendants;

    if(descendants !== '') {
      const descendantsHash = createDescendantsHash(descendants);

      toggleDisabledStateOfDescendants(descendantsHash, true);
      removeSelectedDescendants(descendantsHash);
    }
  });

  /**
   * Summary. Enables the descendant locations, if any, of a location that is unselected
   */
  $(".location-select").on('select2:unselect', function(e) {
    let descendants = e.params.data.element.dataset.descendants;

    if(descendants !== '') {
      toggleDisabledStateOfDescendants(createDescendantsHash(descendants), false);
    }
  });

  // Call disableDescendantsForSelectedLocations on page load
  disableDescendantsForSelectedLocations();

  /**
   * Summary. Applies the relevant CSS style to the location in the select2 dropdown menu, based on depth
   *          in the Locations tree (stored in data-depth attribute on the option element).
   */
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

  /**
   * Summary. Disables the descendant locations, if any, of a selected location on page load
   *          Necessary for user edit, where locations were previously assigned
   */
  function disableDescendantsForSelectedLocations() {
    $('#id_locations').select2('data').forEach(function(location) {
      let descendants = location.element.getAttribute("data-descendants");

      if(descendants !== '') {
        toggleDisabledStateOfDescendants(createDescendantsHash(descendants), true);
      }
    })
  }

  /**
   * Summary. Toggles the disabled attribute in the option element
   *
   * @param {object}   locationsHash
   * @param {boolean}  disabledState  boolean to indicate if disabled is true or false
   */
  function toggleDisabledStateOfDescendants(locationsHash, disabledState) {
    $(".location-select option").filter(function() {
      return this.value in locationsHash;
    }).prop('disabled', disabledState);
  }

  /**
   * Summary. Removes previously selected descendants from the select2 input field when their
   *          parent location is subsequently chosen by the user
   */
  function removeSelectedDescendants(descendantsHash) {
    let updatedLocations = []

    $('#id_locations').select2('data').forEach(function(element) {
      if(!(element["id"] in descendantsHash)) {
        updatedLocations.push(element["id"]);
      }
    });

    $('#id_locations').val(updatedLocations).trigger('change');
  }

  /**
   * Summary. Creates a hash (object) to facilitate lookup of descendants
   */
  function createDescendantsHash(descendants) {
    let descendantsHash = {};

    JSON.parse(descendants.split(/, */)).forEach(function(element) {
      descendantsHash[element] = true;
    });

    return descendantsHash;
  }
});
