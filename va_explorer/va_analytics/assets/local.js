$(document).ready(function(){
    //var csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    //console.log(csrf_token);
    console.log('LOADED LOCAL SCRIPT');
//===========DASHBOARD==================//
    $('#download-data-button').click(function() { 
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "dashboard", message: "Downloaded data from dashboard"}
        });
    });

});

