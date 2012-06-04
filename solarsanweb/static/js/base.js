
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

$(function() {

if ('graphs_hidden' in SolarSan.Settings) {
    if (SolarSan.Settings.graphs_hidden)
        $('#graphs').show();
    else
        $('#graphs').hide();
}

});


