odoo.define('mtd.module.js', function (require) { 
    'use strict';

    var Widget = require('web.Widget');
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;

    var mtd_js = Widget.extend({
        start: function() {
            var self = this;
            var screens = 'width='+ screen.width + '&height=' + screen.height + '&scaling-factor=' + screen.width/screen.height + '&colour-depth=' + screen.colorDepth;
            var window_size = 'width='+ screen.width + '&height=' + screen.height;


            var x = navigator.plugins.length;
            var txt = x;

            for(var i = 0; i < x; i++) {
                txt += navigator.plugins[i].name + ",";
            }

            var str = txt;
            var result= str.slice(1, -1);
            var browser_plugin = result.replace(/ /g, "%20");

            self.rpc("/web/mtd/js", {'js_user_agent': navigator.userAgent, 'window_size':window_size, 'screens': screens, 'browser_plugin': browser_plugin});
        },
    });
    var app = new mtd_js();
    app.start();
});
