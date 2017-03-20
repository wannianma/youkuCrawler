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
	var re = new RegExp('snssdk.com\/video', 'g');
	var res = re.exec(req.url);
	if (res.index > 0) {
            console.log(req.url);
	}
    };

    page.onError = function(msg, trace) {

        var msgStack = ['ERROR: ' + msg];
        if (trace && trace.length) {
                msgStack.push('TRACE:');
                trace.forEach(function(t) {
                msgStack.push(' -> ' + t.file + ': ' + t.line + (t.function ? ' (in function "' + t.function +'")' : ''));
            });
        }
        console.err(msgStack.join('\n'));
    };

    page.open(address, function (status) {
        if (status !== 'success') {
            console.log('error');
        }
        phantom.exit(1);
    });
}
