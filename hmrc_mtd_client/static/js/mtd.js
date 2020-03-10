odoo.define('mtd.module.js', function (require) { 
    'use strict';

    var Widget = require('web.Widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;
    var rpc = require('web.rpc');
    require('web.dom_ready');
    
    var mtd_js = Widget.extend({    
        start: function() {
            var window_size = 'width='+ screen.width + '&height=' + screen.height + '&colour-depth=' + screen.colorDepth + '&scaling-factor=' + 1.25;
            var x = navigator.plugins.length;
            var txt = x;

            for(var i = 0; i < x; i++) {
                txt += navigator.plugins[i].name + ",";
            }

            var str = txt;
            var result= str.slice(1, -1);
            var browser_plugin = result.replace(/ /g, "%20");

            rpc.query({
                model: 'mtd.fraud.prevention',
                method: 'set_java_script_headers',
                args: [{'js_user_agent': navigator.userAgent, 'window_size':window_size, 'screens': window_size, 'browser_plugin': browser_plugin}]
            })
        },
    });
    var app = new mtd_js();
    app.start();
});
