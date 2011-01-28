ROOT = /media/Disk/toolchain/toolchain
box = dm800
arch = mipsel

SIGC_CFLAGS = -I${ROOT}/${box}/build/tmp/staging/${arch}-linux/lib/sigc++-1.2/include -I${ROOT}/${box}/build/tmp/staging/${arch}-linux/include/sigc++-1.2  
PYTHON_CPPFLAGS = -I${ROOT}/${box}/build/tmp/staging/${arch}-linux/include/python2.5
CXX = ${ROOT}/tmp/cross/bin/${arch}-linux-g++
CXXFLAGS = -I${ROOT}/tmp/staging/${arch}-linux/include -fexpensive-optimizations -fomit-frame-pointer -frename-registers -O2 -fpermissive
ENIGMA2_CFLAGS= -I${ROOT}/${box}/build/tmp/staging/${arch}-linux/include/enigma2/ -I${ROOT}/${box}/build/tmp/staging/${arch}-linux/include/
LDFLAGS = -L${ROOT}/tmp/staging/${arch}-linux/lib -Wl,-rpath-link,${ROOT}/tmp/staging/${arch}-linux/lib -Wl,-O1



OBJS := servicewebts.cpp

-include $(OBJS:.cpp=.d)

servicewebts.so:
	$(CXX) -MD $(CXXFLAGS) $(ENIGMA2_CFLAGS) $(SIGC_CFLAGS) \
	$(PYTHON_CPPFLAGS) $(DEFS) -I. -Wall -W $(OBJS) -shared -fPIC \
	-Wl,-soname,servicewebts.so -o servicewebts.so $(LDFLAGS) -D HAVE_DVB_API_VERSION=3 -fno-rtti -fno-exceptions -D DEBUG

all: servicewebts.so

installdir = @INSTALLDIR@
install_DATA = servicewebts.so

CLEANFILES = servicewebts.so servicewebts.d
