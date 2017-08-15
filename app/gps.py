from jnius import PythonJavaClass, java_method, autoclass

Looper = autoclass('android.os.Looper')
LocationManager = autoclass('android.location.LocationManager')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
Context = autoclass('android.content.Context')

class GpsListener(PythonJavaClass):
    __javainterfaces__ = ['android/location/LocationListener']

    def __init__(self, callback):
        super(GpsListener, self).__init__()
        self.callback = callback
        self.locationManager = PythonActivity.mActivity.getSystemService(
                Context.LOCATION_SERVICE)

    def start(self):
        self.locationManager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                0, 100, self, Looper.getMainLooper())

    def stop(self):
        self.locationManager.removeUpdates(self)

    @java_method('()I')
    def hashCode(self):
        return id(self) % 2147483647

    @java_method('(Landroid/location/Location;)V')
    def onLocationChanged(self, location):
        self.callback(self, 'location', location)

    @java_method('(Ljava/lang/String;ILandroid/os/Bundle;)V')
    def onStatusChanged(self, provider, status, extras):
        pass

    @java_method('(Ljava/lang/String;)V')
    def onProviderDisabled(self, status):
        self.callback(self, 'provider-disabled', status)

    @java_method('(Ljava/lang/Object;)Z')
    def equals(self, obj):
        return obj.hashCode() == self.hashCode()
