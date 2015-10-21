# How to install #

Follow the instuctions on  [Build_MobileInsight2 Wiki page](http://metro.cs.ucla.edu/mobile_insight/mediawiki/index.php/Build_MobileInsight2) to build and install the app.

# How to use #

The app has 3 functions at the point of writing:

1. Run a (foreground) script on the phone, and display its output on the screen (only for debug purpose).
2. Select and run an app in a background process, which continues to run even the foreground app is closed.
An app is just a Python script, but has a ".mi2app" extension and is located under the res/ directory.
3. Start and stop trace collection, similar to MobileInsight2 demo (not complete)
