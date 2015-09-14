import ctypes
import numpy as np
from ctypes import byref
MAX_STRING_LENGTH = 512

dll = ctypes.WinDLL('FlyCapture2_C_v100.dll')

class Fc2MACAddress(ctypes.Structure):
    _fields_ = [('octects', ctypes.c_char * 6)]


class Fc2IPAddress(ctypes.Structure):
    _fields_ = [('octects', ctypes.c_char * 4)]


class Fc2ConfigROM(ctypes.Structure):
    _fields_ = [('nodeVendorId', ctypes.c_uint),
                ('nodeVendorId', ctypes.c_uint),
                ('chipIdHi', ctypes.c_uint),
                ('chipIdLo', ctypes.c_uint),
                ('unitSpecId', ctypes.c_uint),
                ('unitSWVer', ctypes.c_uint),
                ('unitSubSWVer', ctypes.c_uint),
                ('vendorUniqueInfo_0', ctypes.c_uint),
                ('vendorUniqueInfo_1', ctypes.c_uint),
                ('vendorUniqueInfo_2', ctypes.c_uint),
                ('vendorUniqueInfo_3', ctypes.c_uint),
                ('pszKeyword', ctypes.c_char * MAX_STRING_LENGTH),
                ('reserved', ctypes.c_uint * 16)]


class Fc2CameraInfo(ctypes.Structure):
    _fields_ = [('serialNumber', ctypes.c_uint),
                ('interfaceType', ctypes.c_uint),
                ('driverType', ctypes.c_uint),
                ('isColorCamera', ctypes.c_uint),
                ('modelName', ctypes.c_char * MAX_STRING_LENGTH),
                ('vendorName', ctypes.c_char * MAX_STRING_LENGTH),
                ('sensorInfo', ctypes.c_char * MAX_STRING_LENGTH),
                ('sensorResolution', ctypes.c_char * MAX_STRING_LENGTH),
                ('driverName', ctypes.c_char * MAX_STRING_LENGTH),
                ('firmwareVersion', ctypes.c_char * MAX_STRING_LENGTH),
                ('firmwareBuildTime', ctypes.c_char * MAX_STRING_LENGTH),
                ('maximumBusSpeed', ctypes.c_uint),
                ('pcieBusSpeed', ctypes.c_uint),
                ('bayerTileFormat', ctypes.c_uint),
                ('busNumber', ctypes.c_ushort),
                ('nodeNumber', ctypes.c_ushort),
                ('iidcVer', ctypes.c_uint),
                ('configROM', Fc2ConfigROM),
                ('gigEMajorVersion', ctypes.c_uint),
                ('gigEMinorVersion', ctypes.c_uint),
                ('userDefinedName', ctypes.c_char * MAX_STRING_LENGTH),
                ('xmlURL1', ctypes.c_char * MAX_STRING_LENGTH),
                ('xmlURL2', ctypes.c_char * MAX_STRING_LENGTH),
                ('fc2MACAddress', Fc2MACAddress),
                ('ipAddress', Fc2IPAddress),
                ('subnetMask', Fc2IPAddress),
                ('defaultGateway', Fc2IPAddress),
                ('ccpStatus', ctypes.c_uint),
                ('applicationIPAddress', ctypes.c_uint),
                ('applicationPort', ctypes.c_uint),
                ('reserved', ctypes.c_uint * 16),]


class Fc2Image(ctypes.Structure):
    _fields_ = [('rows', ctypes.c_uint),
                ('cols', ctypes.c_uint),
                ('stride', ctypes.c_uint),
                ('pData', ctypes.c_void_p), # Cast to long on assignment.
                ('dataSize', ctypes.c_uint),
                ('receivedDataSize', ctypes.c_uint),
                ('fc2PixelFormat', ctypes.c_uint),
                ('fc2BayerTileFormat', ctypes.c_uint),
                ('fc2ImageImp', ctypes.c_voidp)]


class Camera(object):
    def __init__(self):
        self.context = ctypes.c_voidp()
        self.guid = ctypes.c_uint()
        self.cameraInfo = Fc2CameraInfo()


    def connect(self, index=0):
        c = self.context
        dll.fc2CreateContext(byref(c))
        n = ctypes.c_uint()
        dll.fc2GetNumOfCameras(c, byref(n))
        if n == 0:
            raise Exception('No camera found.')
        dll.fc2GetCameraFromIndex(c, index, byref(self.guid))
        dll.fc2Connect(c, byref(self.guid))
        dll.fc2GetCameraInfo(c, byref(self.cameraInfo))


    def grabImageToDisk(self, outFileName='fc2Test.png'):
        c = self.context
        imgRaw = Fc2Image()
        imgConv = Fc2Image()

        dll.fc2CreateImage(byref(imgRaw))
        dll.fc2CreateImage(byref(imgConv))
        dll.fc2StartCapture(c)
        dll.fc2RetrieveBuffer(c, byref(imgRaw))
        dll.fc2StopCapture(c)
        dll.fc2ConvertImageTo(0x80000008,
                              byref(imgRaw),
                              byref(imgConv))
        dll.fc2SaveImage(byref(imgConv),
                         outFileName,
                         -1)
        dll.fc2DestroyImage(byref(imgRaw))
        dll.fc2DestroyImage(byref(imgConv))


    def grabImageToBuffer(self):
        c = self.context
        imgRaw = Fc2Image()
        dll.fc2CreateImage(byref(imgRaw))
        dll.fc2StartCapture(c)
        dll.fc2RetrieveBuffer(c, byref(imgRaw))
        dll.fc2StopCapture(c)

        # When the DLL assignes to imgRaw.pData, it becomes a long in python.
        # Recast to a pointer to a byte array.
        p = ctypes.cast(imgRaw.pData, ctypes.POINTER(ctypes.c_ubyte))
        data = np.fromiter(p, np.uint8, imgRaw.cols * imgRaw.rows)
        self.lastImage = data.reshape((imgRaw.rows, imgRaw.cols))
        dll.fc2DestroyImage(byref(imgRaw))
