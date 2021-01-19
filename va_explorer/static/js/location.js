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
   *          Must explicitly set the width here due to showing/hiding of select2, which
   *          can interfere with the width: https://select2.org/appearance#container-width
   */
  $(".location-restrictions-select").select2({
    placeholder: "Search for location(s) to add to user's geographic access",
    templateResult: formatResult,
    width:'100%'
  });

  /**
   * Summary. Disables the descendant locations, if any, of a location that is selected
   *          Removes any previously-selected descendant locations from the select2 input field
   */
  $(".location-restrictions-select").on('select2:select', function(e) {
    let descendants = e.params.data.element.dataset.descendants;

    if(descendants !== undefined) {
      const descendantsHash = createDescendantsHash(descendants);

      toggleDisabledStateOfDescendants(descendantsHash, true);
      removeSelectedDescendants(descendantsHash);
    }
  });

  /**
   * Summary. Enables the descendant locations, if any, of a location that is unselected
   */
  $(".location-restrictions-select").on('select2:unselect', function(e) {
    let descendants = e.params.data.element.dataset.descendants;

    if(descendants !== undefined) {
      toggleDisabledStateOfDescendants(createDescendantsHash(descendants), false);
    }
  });

  /**
   * Functions to call on page load
   *
   */
  toggleLocationRestrictions();
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
    $('#id_location_restrictions').select2('data').forEach(function(location) {
      let descendants = location.element.getAttribute("data-descendants");

      // Note: getAttribute returns null if the attribute does not exist
      if(descendants !== null) {
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
    $(".location-restrictions-select option").filter(function() {
      return this.value in locationsHash;
    }).prop('disabled', disabledState);
  }

  /**
   * Summary. Removes previously selected descendants from the select2 input field when their
   *          parent location is subsequently chosen by the user
   */
  function removeSelectedDescendants(descendantsHash) {
    let updatedLocations = []

    $('#id_location_restrictions').select2('data').forEach(function(element) {
      if(!(element["id"] in descendantsHash)) {
        updatedLocations.push(element["id"]);
      }
    });

    $('#id_location_restrictions').val(updatedLocations).trigger('change');
  }

  /**
   * Summary. Creates a hash (object) to facilitate lookup of descendants
   */
  function createDescendantsHash(descendants) {
    let descendantsHash = {};

    if (descendants !== undefined) {
      descendants = descendants.replace(/'/g, '"')
    }

    JSON.parse(descendants).forEach(function(element) {
      descendantsHash[element] = true;
    });

    return descendantsHash;
  }

  /**
   * Summary. Hides/shows the locations controls based on the role selected. The controls include:
   *  1. the geographic access radio button
   *  2. the location restrictions select2
   */
  function toggleLocationRestrictions() {
    console.log("The group param is: ")
    console.log($("#id_group option:selected").text());

    // No Role selected (dropdown is blank or undefined)
    if(!$('#id_group option:selected').val()) {
      hideGeographicAccessRadio();
      hideLocationRestrictionsSelect2();
    }
    // Role selected is Field Worker
    else if($('#id_group option:selected').text() === "Field Workers") {
      hideGeographicAccessRadio();
      showLocationRestrictionsSelect2();
    }
    else {
      showGeographicAccessRadio();
      toggleLocationRestrictionsSelect2();
    }
  }

  function hideLocationRestrictionsSelect2() {
    $('#div_id_location_restrictions').hide();
    $('.location-restrictions-select').val(null).trigger('change');
  }

  function showLocationRestrictionsSelect2() {
    $('#div_id_location_restrictions').show();

    // Add the asterisk as a child of the locations label to indicate the field is required, when visible
    if($("label[for='id_location_restrictions']").get(0).children.length===0) {
      $("label[for='id_location_restrictions']").append('<span class="asteriskField">*</span>');
    }
  }

  function showGeographicAccessRadio() {
    $('#div_id_geographic_access').show()
  }

  function hideGeographicAccessRadio() {
    $('#div_id_geographic_access').hide()
  }

  /**
   * Summary. Hides/shows the location select2 dropdown depending on the
   *          value of the geographic_access radio button
   */
  function toggleLocationRestrictionsSelect2(param) {
    if($('input[name="geographic_access"]:checked').val() === "national"){
      hideLocationRestrictionsSelect2()
    }
    else{
      showLocationRestrictionsSelect2();
    }
  }

  /**
   * Summary. Event handler that listens for the change of role assignment
   */
  $('#id_group').change(function() {
    toggleLocationRestrictions(this);
  });

  /**
   * Summary. Event handler that listens for the change of geographic access
   *          from location-specific to national
   */
  $('input[type=radio][name=geographic_access]').on('change',function(){
    toggleLocationRestrictionsSelect2();
  });
});
