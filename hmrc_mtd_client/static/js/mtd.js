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
            console.log('start');
            var window_size = 'width='+ screen.width + '&height=' + screen.height 
            rpc.query({
                model: 'mtd.fraud.prevention',
                method: 'set_java_script_headers',
                args: [{'js_user_agent': navigator.userAgent, 'window_size':window_size, 'screens': window_size}]
            })
        },
    
    });
    var app = new mtd_js();
    app.start();
});
    