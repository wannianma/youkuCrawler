// Read the Phantom webpage '#intro' element text using jQuery and "includeJs"

"use strict";
var page = require('webpage').create(),
    system = require('system'),
    url;

//page.viewportSize = {width: 4800,height: 8000};
page.settings.loadImages = false;
page.settings.userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36';
page.settings.resourceTimeout = 2000;
page.onConsoleMessage = function(msg) {
    console.log(msg);
};

if (system.args.length === 1) {
    phantom.exit(1);
} else {
    url = system.args[1];
    page.open(url, function(status) {
    // Checks for bottom div and scrolls down from time to time
    var count = 0;
    window.setInterval(function() {
      if(count != page.content.match(/class="yk-col4"/g).length) { // Didn't find
        count = page.content.match(/class="yk-col4"/g).length;
        page.evaluate(function() {
          // Scrolls to the bottom of page
          window.document.body.scrollTop = document.body.scrollHeight;
        });
      }
      else { 
        //page.render('youku.png');
        console.log(page.content);
        phantom.exit();
      }
    }, 1000);
});
}

