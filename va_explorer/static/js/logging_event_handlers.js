$(document).ready(function(){

    var log_url = "/va_logs/submit_log"

    //===========HOME==================//
    $('#additional-issues').click(function() {
        $.ajax({
            url: log_url,
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
            url: log_url,
            method: 'POST',
            data: {name: "data_mgnt", message: "Clicked view tab for VA " + getRecordId() }
        });
    });

    $('#issues-tab').click(function() {
        $.ajax({
            url: log_url,
            method: 'POST',
            data: {name: "data_mgnt", message: "Clicked issues tab for VA " + getRecordId()}
        });
    });

    $('#history-tab').click(function() {
        $.ajax({
            url: log_url,
            method: 'POST',
            data: {name: "data_mgnt", message: "Clicked history tab for VA " + getRecordId()}
        });
    });

//===========DASHBOARD==================//
    $('#download-data-button').click(function() {
        $.ajax({
            url: log_url,
            method: 'POST',
            data: {name: "dashboard", message: "Downloaded data from dashboard"}
        });
    });

    $('#cod_tab').click(function() {
        $.ajax({
            url: log_url,
            method: 'POST',
            data: {name: "dashboard", message: "Switched to COD Tab"}
        });
    });
    $('#trend_tab').click(function() {
        $.ajax({
            url: log_url,
            method: 'POST',
            data: {name: "dashboard", message: "Switched to VA Trends Tab"}
        });
    });
    $('#demographic_tab').click(function() {
        $.ajax({
            url: log_url,
            method: 'POST',
            data: {name: "dashboard", message: "Switched to Demographics Tab"}
        });
    });
});

