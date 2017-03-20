"use strict";
var page = require('webpage').create(),
    system = require('system'),
    address;

if (system.args.length === 1) {
    console.log('Usage: netlog.js <some URL>');
    phantom.exit(1);
} else {
    address = system.args[1];

    page.onResourceRequested = function (req) {
	var re = new RegExp('playurl', 'g');
	var res = re.exec(req.url);
	if (res.index > 0) {
            console.log(req.url);
	}
    };

    page.open(address, function (status) {
        if (status !== 'success') {
            console.log('error');
        }
        phantom.exit();
    });
}
