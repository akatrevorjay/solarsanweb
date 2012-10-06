
requirejs.config({
    //By default load any module IDs from js/lib
    baseUrl: '/static/js',
    //except, if the module ID starts with "app",
    //load it from the js/app directory. paths
    //config is relative to the baseUrl, and
    //never includes a ".js" extension since
    //the paths config could be for a directory.
    paths: {
        //'3rd': '../3rd',
        bootstrap: '../bootstrap/js',
    },
    shim: {
        //'jquery.colorize': ['jquery'],
        //'jquery.scroll': ['jquery'],
        //'backbone.layoutmanager': ['backbone'],
        'backbone': {
            //These script dependencies should be loaded before loading
            //backbone.js
            deps: ['underscore', 'jquery'],
            //Once loaded, use the global 'Backbone' as the
            //module value.
            exports: 'Backbone'
        },
        'underscore': {
            exports: '_',
        },
        'jquery': {
            exports: function(jq){
                window.jQuery = this.$;
                return window.jQuery;
            },
        },
        /*
        'foo': {
            deps: ['bar'],
            exports: 'Foo',
            init: function (bar) {
                //Using a function allows you to call noConflict for
                //libraries that support it, and do other cleanup.
                //However, plugins for those libraries may still want
                //a global. "this" for the function will be the global
                //object. The dependencies will be passed in as
                //function arguments. If this function returns a value,
                //then that value is used as the module export value
                //instead of the object found via the 'exports' string.
                return this.Foo.noConflict();
            }
        }
        */
        'd3': ['jquery'],
        'nvd3': ['d3'],
        'cubism': {
            deps: ['d3'],
            exports: 'cubism',
        },
        //'jquery.gritter': ['jquery'],
        'backbone-tastypie': ['backbone'],
        'backbone-relational': ['backbone'],
        //'base': ['cubism', 'nvd3'],
        'django.mustache': ['mustache'],
        'chosen.jquery': {
            deps: ['jquery'],
            exports: 'jQuery.fn.chosen',
        },
        'jquery.gritter': {
            deps: ['jquery'],
            exports: 'jQuery.fn.gritter',
        },
        'bootstrap/bootstrap': {
            deps: ['jquery'],
            //exports: 'jQuery.fn.tooltip'
        },
        'debug_toolbar': ['jquery'],
    }
});

// Start the main app logic.
//requirejs(['jquery', 'canvas', 'app/sub'],
//function   ($,        canvas,   sub) {
//    //jQuery, canvas and the app/sub module are all
//    //loaded and can be used here now.
//});

require([
    'jquery',
    'bootstrap/bootstrap',
    'd3',
    'jquery.gritter',
    'chosen.jquery',
    'underscore',
    'cubism',
    'nvd3',
    'backbone',
    'backbone-relational',
    'backbone-tastypie',
    'mustache',
    'django.mustache',
    'base',
    'debug_toolbar',
    ], function($) {

    console.log('done main');
});

//});
