
/* ____
 * main
 */
var SolarSan = {};

SolarSan.CookieParams = {name: 'SolarSanSettings', opts: { expires: 365, path: '/' }};
SolarSan.get = function() {
    SolarSan.Settings = $.JSONCookie(SolarSan.CookieParams.name);
};
SolarSan.set = function(data) {
    if (data)
        $.extend(SolarSan.Settings, data);
    $.JSONCookie(SolarSan.CookieParams.name, SolarSan.Settings, SolarSan.CookieParams.opts);
};
SolarSan.get();

function graphs_toggle() {
    var graphs = $('#graphs');
    graphs.toggle();
    SolarSan.set({ 'graphs_hidden': graphs.is(':hidden') });
}

$(document).ready(function(){

if ('graphs_hidden' in SolarSan.Settings) {
    if (SolarSan.Settings.graphs_hidden)
        $('#graphs').show();
    else
        $('#graphs').hide();
}

});


//$(document).ready(function(){
//// The initial load event will try and pull the cookie to see if the toggle is "open"
//var openToggle = getCookie("open") || false;
//if ( openToggle )
//    $("#Header").show();
//else
//    $("#Header").hide();

//// The click handler will decide whether the toggle should "show"/"hide" and set the cookie.
//$('#btnToggleHeader').click(function() {
//    var closed = $("#Header").is(":hidden");
//    if ( closed )
//       $("#Header").show();
//    else
//        $("#Header").hide();
//    setCookie("open", !closed, 365 );
//});

//});


