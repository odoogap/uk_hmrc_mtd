odoo.define('mtd.module.js', function (require) { 
    'use strict';

    var Widget = require('web.Widget');
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;
    
    var mtd_js = Widget.extend({    
        start: function() {
            console.log('start');
            var self = this;
            var window_size = 'width='+ screen.width + '&height=' + screen.height 
            self.rpc("/web/mtd/js", {'js_user_agent': navigator.userAgent, 'window_size':window_size, 'screens': window_size});
        },
    });
    var app = new mtd_js();
    app.start();
});
