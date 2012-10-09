/**
 * Cookie plugin
 *
 * Copyright (c) 2006 Klaus Hartl (stilbuero.de)
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 */

/**
 * Create a cookie with the given name and value and other optional parameters.
 *
 * @example $.cookie('the_cookie', 'the_value');
 * @desc Set the value of a cookie.
 * @example $.cookie('the_cookie', 'the_value', { expires: 7, path: '/', domain: 'jquery.com', secure: true });
 * @desc Create a cookie with all available options.
 * @example $.cookie('the_cookie', 'the_value');
 * @desc Create a session cookie.
 * @example $.cookie('the_cookie', null);
 * @desc Delete a cookie by passing null as value. Keep in mind that you have to use the same path and domain
 *       used when the cookie was set.
 *
 * @param String name The name of the cookie.
 * @param String value The value of the cookie.
 * @param Object options An object literal containing key/value pairs to provide optional cookie attributes.
 * @option Number|Date expires Either an integer specifying the expiration date from now on in days or a Date object.
 *                             If a negative value is specified (e.g. a date in the past), the cookie will be deleted.
 *                             If set to null or omitted, the cookie will be a session cookie and will not be retained
 *                             when the the browser exits.
 * @option String path The value of the path atribute of the cookie (default: path of page that created the cookie).
 * @option String domain The value of the domain attribute of the cookie (default: domain of page that created the cookie).
 * @option Boolean secure If true, the secure attribute of the cookie will be set and the cookie transmission will
 *                        require a secure protocol (like HTTPS).
 * @type undefined
 *
 * @name $.cookie
 * @cat Plugins/Cookie
 * @author Klaus Hartl/klaus.hartl@stilbuero.de
 */

/**
 * Get the value of a cookie with the given name.
 *
 * @example $.cookie('the_cookie');
 * @desc Get the value of a cookie.
 *
 * @param String name The name of the cookie.
 * @return The value of the cookie.
 * @type String
 *
 * @name $.cookie
 * @cat Plugins/Cookie
 * @author Klaus Hartl/klaus.hartl@stilbuero.de
 */
jQuery.cookie = function(name, value, options) {
    if (typeof value != 'undefined') { // name and value given, set cookie
        options = options || {};
        if (value === null) {
            value = '';
            options.expires = -1;
        }
        var expires = '';
        if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) {
            var date;
            if (typeof options.expires == 'number') {
                date = new Date();
                date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
            } else {
                date = options.expires;
            }
            expires = '; expires=' + date.toUTCString(); // use expires attribute, max-age is not supported by IE
        }
        // CAUTION: Needed to parenthesize options.path and options.domain
        // in the following expressions, otherwise they evaluate to undefined
        // in the packed version for some reason...
        var path = options.path ? '; path=' + (options.path) : '';
        var domain = options.domain ? '; domain=' + (options.domain) : '';
        var secure = options.secure ? '; secure' : '';
        document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join('');
    } else { // only name given, get cookie
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};window.djdt = (function(window, document, jQuery) {
	jQuery.cookie = function(name, value, options) { if (typeof value != 'undefined') { options = options || {}; if (value === null) { value = ''; options.expires = -1; } var expires = ''; if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) { var date; if (typeof options.expires == 'number') { date = new Date(); date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000)); } else { date = options.expires; } expires = '; expires=' + date.toUTCString(); } var path = options.path ? '; path=' + (options.path) : ''; var domain = options.domain ? '; domain=' + (options.domain) : ''; var secure = options.secure ? '; secure' : ''; document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join(''); } else { var cookieValue = null; if (document.cookie && document.cookie != '') { var cookies = document.cookie.split(';'); for (var i = 0; i < cookies.length; i++) { var cookie = $.trim(cookies[i]); if (cookie.substring(0, name.length + 1) == (name + '=')) { cookieValue = decodeURIComponent(cookie.substring(name.length + 1)); break; } } } return cookieValue; } };
	var $ = jQuery;
	var COOKIE_NAME = 'djdt';
	var djdt = {
		jQuery: jQuery,
		events: {
			ready: []
		},
		isReady: false,
		init: function() {
			$('#djDebug').show();
			var current = null;
			$('#djDebugPanelList li a').live('click', function() {
				if (!this.className) {
					return false;
				}
				current = $('#djDebug #' + this.className);
				if (current.is(':visible')) {
					$(document).trigger('close.djDebug');
					$(this).parent().removeClass('active');
				} else {
					$('.panelContent').hide(); // Hide any that are already open
					current.show();
					$('#djDebugToolbar li').removeClass('active');
					$(this).parent().addClass('active');
				}
				return false;
			});
			$('#djDebug a.djDebugClose').live('click', function() {
				$(document).trigger('close.djDebug');
				$('#djDebugToolbar li').removeClass('active');
				return false;
			});
			$('#djDebug a.remoteCall').live('click', function() {
				$('#djDebugWindow').load(this.href, function(response, status, xhr) {
					if (status == "error") {
						var message = '<div class="djDebugPanelTitle"><a class="djDebugClose djDebugBack" href="">Back</a><h3>'+xhr.status+': '+xhr.statusText+'</h3></div>';
						$('#djDebugWindow').html(message);
					}
					$('#djDebugWindow a.djDebugBack').live('click', function() {
						$(this).parent().parent().hide();
						return false;
					});
				});
				$('#djDebugWindow').show();
				return false;
			});
			$('#djDebugTemplatePanel a.djTemplateShowContext').live('click', function() {
				djdt.toggle_arrow($(this).children('.toggleArrow'));
				djdt.toggle_content($(this).parent().next());
				return false;
			});
			$('#djDebug a.djDebugToggle').live('click', function(e) {
				e.preventDefault();
				$(this).parent().find('.djDebugCollapsed').toggle();
				$(this).parent().find('.djDebugUncollapsed').toggle();
			});
			$('#djDebug a.djToggleSwitch').live('click', function(e) {
				e.preventDefault();
				var btn = $(this);
				var id = btn.attr('data-toggle-id');
				var open_me = btn.text() == btn.attr('data-toggle-open');
				if (id === '' || !id) {
					return;
				}
				var name = btn.attr('data-toggle-name');
				btn.parents('.djDebugPanelContent').find('#' + name + '_' + id).find('.djDebugCollapsed').toggle(open_me);
				btn.parents('.djDebugPanelContent').find('#' + name + '_' + id).find('.djDebugUncollapsed').toggle(!open_me);
				$(this).parents('.djDebugPanelContent').find('.djToggleDetails_' + id).each(function(){
					var $this = $(this);
					if (open_me) {
						$this.addClass('djSelected');
						$this.removeClass('djUnselected');
						btn.text(btn.attr('data-toggle-close'));
						$this.find('.djToggleSwitch').text(btn.text());
					} else {
						$this.removeClass('djSelected');
						$this.addClass('djUnselected');
						btn.text(btn.attr('data-toggle-open'));
						$this.find('.djToggleSwitch').text(btn.text());
					}
				});
				return;
			});
			function getSubcalls(row) {
				var id = row.attr('id');
				return $('.djDebugProfileRow[id^="'+id+'_"]');
			}
			function getDirectSubcalls(row) {
				var subcalls = getSubcalls(row);
				var depth = parseInt(row.attr('depth'), 10) + 1;
				return subcalls.filter('[depth='+depth+']');
			}
			$('.djDebugProfileRow .djDebugProfileToggle').live('click', function(){
				var row = $(this).closest('.djDebugProfileRow');
				var subcalls = getSubcalls(row);
				if (subcalls.css('display') == 'none') {
					getDirectSubcalls(row).show();
				} else {
					subcalls.hide();
				}
			});
			$('#djHideToolBarButton').click(function() {
				djdt.hide_toolbar(true);
				return false;
			});
			$('#djShowToolBarButton').click(function() {
				djdt.show_toolbar();
				return false;
			});
			$(document).bind('close.djDebug', function() {
				// If a sub-panel is open, close that
				if ($('#djDebugWindow').is(':visible')) {
					$('#djDebugWindow').hide();
					return;
				}
				// If a panel is open, close that
				if ($('.panelContent').is(':visible')) {
					$('.panelContent').hide();
					return;
				}
				// Otherwise, just minimize the toolbar
				if ($('#djDebugToolbar').is(':visible')) {
					djdt.hide_toolbar(true);
					return;
				}
			});
			if ($.cookie(COOKIE_NAME)) {
				djdt.hide_toolbar(false);
			} else {
				djdt.show_toolbar(false);
			}
			$('#djDebug .djDebugHoverable').hover(function(){
				$(this).addClass('djDebugHover');
			}, function(){
				$(this).removeClass('djDebugHover');
			});
			djdt.isReady = true;
			$.each(djdt.events.ready, function(_, callback){
				callback(djdt);
			});
		},
		toggle_content: function(elem) {
			if (elem.is(':visible')) {
				elem.hide();
			} else {
				elem.show();
			}
		},
		close: function() {
			$(document).trigger('close.djDebug');
			return false;
		},
		hide_toolbar: function(setCookie) {
			// close any sub panels
			$('#djDebugWindow').hide();
			// close all panels
			$('.panelContent').hide();
			$('#djDebugToolbar li').removeClass('active');
			// finally close toolbar
			$('#djDebugToolbar').hide('fast');
			$('#djDebugToolbarHandle').show();
			// Unbind keydown
			$(document).unbind('keydown.djDebug');
			if (setCookie) {
				$.cookie(COOKIE_NAME, 'hide', {
					path: '/',
					expires: 10
				});
			}
		},
		show_toolbar: function(animate) {
			// Set up keybindings
			$(document).bind('keydown.djDebug', function(e) {
				if (e.keyCode == 27) {
					djdt.close();
				}
			});
			$('#djDebugToolbarHandle').hide();
			if (animate) {
				$('#djDebugToolbar').show('fast');
			} else {
				$('#djDebugToolbar').show();
			}
			$.cookie(COOKIE_NAME, null, {
				path: '/',
				expires: -1
			});
		},
		toggle_arrow: function(elem) {
			var uarr = String.fromCharCode(0x25b6);
			var darr = String.fromCharCode(0x25bc);
			elem.html(elem.html() == uarr ? darr : uarr);
		},
		ready: function(callback){
			if (djdt.isReady) {
				callback(djdt);
			} else {
				djdt.events.ready.push(callback);
			}
		}
	};
	$(document).ready(function() {
		djdt.init();
	});
	return djdt;
}(window, document, jQuery));
