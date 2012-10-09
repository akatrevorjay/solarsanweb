
requirejs.config({
    //By default load any module IDs from js/lib
    baseUrl: '/static/js',

    //except, if the module ID starts with "app",
    //load it from the js/app directory. paths
    //config is relative to the baseUrl, and
    //never includes a ".js" extension since
    //the paths config could be for a directory.
    paths: {
        'jquery': 'jquery',
        //'bootstrap': 'bootstrap',
        bootstrap: '../bootstrap/js',
        //'3rd': '../3rd',
    },

    map: {
        '*': {
            //'jquery': 'adapters/jquery'
            'bootstrap': 'bootstrap/bootstrap',
        },

        /*
        'adapters/jquery': {
            'jquery': 'jquery'
        }
        */
    },

    shim: {
        //'jquery': {
        //    exports: 'jQuery'
        //},

        //'jquery.colorize': ['jquery'],
        //'jquery.scroll': ['jquery'],
        //'backbone.layoutmanager': ['backbone'],

        'backbone': {
            deps: ['underscore'],
            exports: 'Backbone'
        },

        'underscore': {
            exports: '_',
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

        'd3': {
            deps: ['jquery'],
            exports: 'd3'
        },

        'nvd3': {
            deps: ['d3'],
            exports: 'nv'
        },

        'cubism': {
            deps: ['d3'],
            exports: 'cubism'
        },

        'backbone-tastypie': ['backbone'],

        'backbone-relational': ['backbone'],

        //'base': ['cubism', 'nvd3'],

        'mustache': {
            deps: ['jquery'],
        },

        'django.mustache': {
            deps: ['mustache'],
        },

        'chosen': {
            deps: ['jquery'],
            exports: 'jQuery.fn.chosen',
        },

        'jquery.gritter': {
            deps: ['jquery'],
            exports: 'jQuery.fn.gritter',
        },

        'bootstrap': {
            deps: ['jquery'],
            //exports: 'jQuery.fn.tooltip'
        }
    }
});

//var $ = null;
define(
    'main',
    [
        'jquery',
        'bootstrap',
        //'d3',
        //'jquery.gritter',
        //'chosen',
        //'undersmain',
        //'cubism',
        //'nvd3',
        //'backbone',
        //'backbone-relational',
        //'backbone-tastypie',
        //'mustache',
        //'django.mustache',
        'debug_toolbar',
    ],
    function ($) {
        // jQuery and bootstrap have been loaded
        console.log('main: got jquery+bootstrap');
        //console.log('main: done; unholding ready.');
        //return $.noConflict(true);

        require(['jquery', 'bootstrap', 'base'], function ($) {
            console.log('main: got base');
        });

        return $;
});

