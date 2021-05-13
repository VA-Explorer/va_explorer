$(document).ready(function(){
    //var csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    //console.log(csrf_token);

    // $("body").bind("ajaxSend", function(elm, xhr, s){
    //    if (s.type == "POST") {
    //       xhr.setRequestHeader('X-CSRFToken', csrf_token);
    //    }
    // });
    //===========HOME==================//
    $('#additional_issues').click(function() { 
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "home", message: "Clicked additional issues link"}
        });
    });
    //===========DATA MANAGEMENT==================//
    // get VA record ID from va data mangement url string
    function getRecordId(){
        url_str = window.location.toString()
        if(url_str.match('show') != null){
            return url_str.split('/').pop()
        }else{
            return "Unknown"
        }
    }

    $('#record-tab').click(function() { 
        getRecordId()
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "data_mgnt", message: "Clicked view tab for VA " + getRecordId() }
        });
    });

    $('#issues-tab').click(function() { 
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "data_mgnt", message: "Clicked issues tab for VA " + getRecordId()}
        });
    });

    $('#history-tab').click(function() { 
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "data_mgnt", message: "Clicked history tab for VA " + getRecordId()}
        });
    });

//===========DASHBOARD==================//
    $('#download-data-button').click(function() { 
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "dashboard", message: "Downloaded data from dashboard"}
        });
    });

    $('#cod_tab').click(function() { 
        console.log('CLICKED COD TAB');
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "dashboard", message: "Switched to COD Tab"}
        });
    });
    $('#trend_tab').click(function() { 
        console.log('CLICKED TREND TAB');
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "dashboard", message: "Switched to VA Trends Tab"}
        });
    });
    $('#demographic_tab').click(function() {
        console.log('CLICKED DEMO TAB'); 
        $.ajax({
            url: '/logs/submit_log',
            method: 'POST',
            data: {name: "dashboard", message: "Switched to Demographics Tab"}
        });
    });


});

