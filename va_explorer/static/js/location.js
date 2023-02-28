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
  $(".facility-restrictions-select").select2({
    placeholder: "Search for facilities to add to Field Worker's geographic access",
    width:'100%'
  });

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
   * Functions to call and variables to define on page load
   *
   */
  const geographicAccessID = 'div_id_geographic_access';
  const locationRestrictionsID= 'div_id_location_restrictions';
  const facilityRestrictionsID = 'div_id_facility_restrictions';

  const locationRestrictionsClass = 'location-restrictions-select';
  const facilityRestrictionsClass = 'facility-restrictions-select';

  updateFormForRoleSelected();
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
   * Update status of Can View PII checkbox depending on whether selected group can view PII.
   */
   function updatePIICheckbox() {
    const groupCanViewPII = Boolean($('#id_group option:selected').data('view-pii'));
    $('#id_view_pii').attr('disabled', groupCanViewPII);
    $('#id_view_pii').attr('checked', groupCanViewPII);
  }

  // On load, if group can view PII, disable checkbox.
  // Don't DISABLE it if the group CAN'T view PII because the user might have it checked explicitly.
  const groupCanViewPII = Boolean($('#id_group option:selected').data('view-pii'));
  if (groupCanViewPII) {
    $('#id_view_pii').attr('disabled', true);
    $('#id_view_pii').attr('checked', true);
  }

  /**
   * Update status of Can Download Data checkbox depending on whether selected group can download data.
   */
   function updateDownloadDataCheckbox() {
    const groupCanDownloadData = Boolean($('#id_group option:selected').data('download-data'));
    $('#id_download_data').attr('disabled', groupCanDownloadData);
    $('#id_download_data').attr('checked', groupCanDownloadData);
  }

  // On load, if group can view PII, disable checkbox.
  // Don't DISABLE it if the group CAN'T view PII because the user might have it checked explicitly.
  const groupCanDownloadData = Boolean($('#id_group option:selected').data('download-data'));
  if (groupCanDownloadData) {
    $('#id_download_data').attr('disabled', true);
    $('#id_download_data').attr('checked', true);
  }


  /**
   * Summary. Hides/shows the form locations controls based on the role selected. The controls include:
   *  1. the geographic access radio button
   *  2. the location restrictions select2 dropdown
   *  3. the facility restrictions select2 dropdown (visible for Field Worker role only)
   */
  function updateFormForRoleSelected() {
    let elemToHide = [];
    let elemToShow = [];
    let select2ToClear = [];
    let fieldToClear = [];

    // No Role selected (dropdown is blank or undefined)
    if(!$('#id_group option:selected').val()) {
      elemToHide.push(
          geographicAccessID,
          locationRestrictionsID,
          facilityRestrictionsID
      );
      select2ToClear.push(locationRestrictionsClass, facilityRestrictionsClass);
    }

    // Role selected is Field Worker
    else if($('#id_group option:selected').text() === "Field Workers") {
      elemToHide.push(geographicAccessID, locationRestrictionsID);
      elemToShow.push(facilityRestrictionsID);
      select2ToClear.push(locationRestrictionsClass);

      // Add asterisk to facility restrictions select2 indicating it is required
      addRequiredAsterisk();

      // Check the location-specific radio to true, which has been hidden
      $("input[name=geographic_access]").val(["location-specific"]);
    }

    // Role selected is not Field Worker (Admin, Data Manager, Data Viewer)
    else {
      elemToHide.push(facilityRestrictionsID);
      elemToShow.push(geographicAccessID);
      select2ToClear.push(facilityRestrictionsClass);

      // This method will determine if the locationRestrictions select2 should be shown/hidden
      updateFormForGeographicAccess();
    }

    // Show/hide the appropriate elements
    elemToHide.forEach(elem => $('#' + elem).hide());
    elemToShow.forEach(elem =>$('#' + elem).show());

    // Clear the appropriate elements
    select2ToClear.forEach(select2 => $('.' + select2).val(null).trigger('change'));
    fieldToClear.forEach(elem => $('#' + elem).val(''));

    addRequiredAsterisk();
  }

  /**
   * Summary. Adds a span with an asterisk to facility restrictions and location restrictions
   *          as a visual cue to the user that the field is required
   */
  function addRequiredAsterisk() {
    [
        $("label[for='id_location_restrictions']"),
        $("label[for='id_facility_restrictions']")
    ].forEach(function(elem){
      if(elem && elem.children().length==0) {
        elem.append('<span class="asteriskField">*</span>');
      }
    })
  }

  /**
   * Summary. Hides/shows the location select2 dropdown depending on the
   *          value of the geographic_access radio button
   */
  function updateFormForGeographicAccess() {
    if($('input[name="geographic_access"]:checked').val() === "national") {
      $('#' + locationRestrictionsID).hide();
      $('.' + locationRestrictionsClass).val(null).trigger('change');
    }
    else{
      $('#' + locationRestrictionsID).show();
    }
  }

  /**
   * Summary. Event handler that listens for the change of role assignment
   */
  $('#id_group').change(function() {
    updateFormForRoleSelected();
    updatePIICheckbox();
    updateDownloadDataCheckbox();
  });

  /**
   * Summary. Event handler that listens for the change of geographic access
   *          from location-specific to national
   */
  $('input[type=radio][name=geographic_access]').on('change',function(){
    updateFormForGeographicAccess();
  });
});
