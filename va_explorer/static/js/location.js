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

  // var test = $('.js-example-basic-single');
  // test.unbind();
  // test.on("select2:select", function(event) {
  //   var selected = $(event.currentTarget).find("option:selected");
  //   var label = selected.text();
  //   var value = selected.val();
  //   $("<span class=\"badge badge-pill badge-info\" style=\"margin-right: 5px;\">\n" +
  //       label +
  //       "</span>").appendTo("div#added_locations");
  //   console.log(value);
  //   console.log(label);
  // });

  var url = $("#user-create-form").attr("data-location-url");

  $("select#id_location_1").unbind();
  $("select#id_location_1").change(function() {
    const locationIds = $(this).val();

    $("#id_location_2").removeClass("hidden");
    $("div#location_message").empty();

    if(!$("#id_location_3").hasClass("hidden")){
      $("#id_location_3").addClass("hidden");
    }

    $.ajax({
      url: url,
      data: {
        'location': locationIds
      },
      success: function(data) {
        $("#id_location_2").html(data); // replace the contents of location 2 input with the data from the server
        $("#id_location_3").html([]);
      }
    });
  });

  $("select#id_location_2").unbind();
  $("select#id_location_2").change(function() {
    const locationIds = $(this).val();

    if(!$("#id_location_3").hasClass("hidden")){
      $("#id_location_3").addClass("hidden");
    }
    $("div#location_message").empty();

    $.ajax({
      url: url,
      data: {
        'location': locationIds
      },
      success: function(data) {
        if($.trim(data).length > 0) {
          $("#id_location_3").removeClass("hidden").html(data); // replace the contents of location 3 input with the data from the server
        }
        else {
          $("#id_location_3").html(data);
          $("<p>No locations returned.</p>").appendTo("div#location_message");
        }
      }
    });
  });
});
