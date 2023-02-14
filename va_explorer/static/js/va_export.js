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
   * Summary. Initializes all select2 dropdowns
   *          Must explicitly set the width here due to showing/hiding of select2, which
   *          can interfere with the width: https://select2.org/appearance#container-width
   */

  $(".cod-select").select2({
    placeholder: "Filter data by Cause of Death (CoD)",
    width:'100%'
  });

  $(".location-restrictions-select").select2({
    placeholder: "Search for location(s) from which to download data",
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
  const locationRestrictionsID= 'div_id_locations';
  const downloadFormatID = 'div_id_format';
  const exportEndpointID = 'div_id_export_config';


  const locationRestrictionsClass = 'location-restrictions-select';
  const facilityRestrictionsClass = 'facility-restrictions-select';

  updateFormForActionSelected();
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

    if (descendants !== undefined) {
      descendants = descendants.replace(/'/g, '"')
    }

    JSON.parse(descendants).forEach(function(element) {
      descendantsHash[element] = true;
    });

    return descendantsHash;
  }


  /**
   * Summary. Hides/shows the form locations controls based on the role selected. The controls include:
   *  1. the geographic access radio button
   *  2. the location restrictions select2 dropdown
   *  3. the facility restrictions select2 dropdown (visible for Field Worker role only)
   */
  function updateFormForActionSelected() {
    let elemToHide = [];
    let elemToShow = [];

    // chose to export data (to external endpoint)
    if($('#id_action option:selected').text() == "Export Data") {
      elemToHide.push(downloadFormatID);
      elemToShow.push(exportEndpointID);
    }

    // chose to download data (to local file)
    else if ($('#id_action option:selected').text() == "Download Data") {
      elemToHide.push(exportEndpointID);
      elemToShow.push(downloadFormatID);

    }
    // placeholder for other future actions
    else{
      elemToHide = []
      elemToShow = []
    }

    // Show/hide the appropriate elements
    elemToHide.forEach(elem => $('#' + elem).hide());
    elemToShow.forEach(elem =>$('#' + elem).show());

  }

  /**
   * Summary. Changes text of submit button to reflect user action.
   */
  function updateSubmitText() {
    if($('#id_action option:selected').text() == "Export Data") {
      $("#submit-form").text("Export");
      // #TODO: remove this once we get export working
      $("#submit-form").prop("disabled", true);
    }
    else if($("#id_action option:selected").text() == "Download Data"){
      $("#submit-form").text("Download");
    }
  }

  /**
   * Summary. Event handler that listens for the change of export action
   */
  $('#id_action').change(function() {
    // show/hide appropriate fields
    updateFormForActionSelected();
    // change submit button text
    updateSubmitText();
  });

  /**
   * Summary. Event handler for form submit
   */
  $('#export-form').on('submit', function(event){
   event.preventDefault();
   create_export();
  });

  /**
   * Summary. Sends the export form via XMLHttpRequest and POST method; creates download
   *  Uses the approach here: https://stackoverflow.com/questions/51675844/django-download-excel-file-with-ajax
   */
  const create_export = () => {
    let request = new XMLHttpRequest();
    request.open('POST', "/va_export/verbalautopsy/", true);
    request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
    // Response type must be arraybuffer
    request.responseType = 'arraybuffer';

    const data = $('#export-form').serialize();

    // Show the download modal before the request is sent
    $('#downloadModal').modal('show');

    request.onload = function (e) {
      // Hide the download modal when the request returns, regardless of the status code returned
      $('#downloadModal').modal('hide');
      if (this.status === 200) {
        let filename = "";
        let disposition = request.getResponseHeader('Content-Disposition');
        // Check if filename is given
        if (disposition && disposition.indexOf('attachment') !== -1) {
          let filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
          let matches = filenameRegex.exec(disposition);
          if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
        }
        const blob = this.response;
        if (window.navigator.msSaveOrOpenBlob) {
          window.navigator.msSaveBlob(blob, filename);
        }
        else {
          let downloadLink = window.document.createElement('a');
          const contentTypeHeader = request.getResponseHeader("Content-Type");

          downloadLink.href = window.URL.createObjectURL(new Blob([blob], {type: contentTypeHeader}));
          downloadLink.download = filename;
          document.body.appendChild(downloadLink);
          downloadLink.click();
          document.body.removeChild(downloadLink);
        }
      }
      else {
        // Show the downloadFailed modal if we don't receive a status code of 200
        // TODO: Write to error log
        $('#downloadFailedModal').modal('show');
      }
    };
    request.send(data);
  }
  // Shows the submit button when the page is completely loaded
  // This is required because we are posting the form via JS, so we need to ensure that this file loads before
  // the user can submit the form)
  $('#submit-form').removeClass('hidden');
});
