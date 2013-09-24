#Define where is your duckbox toolchain
duckbox_path ?= /home/tech/tdt-amiko
#And what box do you have
CUBEREVO =
CUBEREVO_MINI =
CUBEREVO_MINI2 =
CUBEREVO_MINI_FTA =
CUBEREVO_250HD =
CUBEREVO_2000HD =
CUBEREVO_9500HD =
UFS910 =
UFS922 =
TF7700 =
FLASH_UFS910 =
FORTIS_HDBOX =
ATEVIO7500 =
HL101 =
VIP1_V2 =
VIP2_V1 =
OCTAGON1008 =
UFS912 =
SPARK = 1
SPARK7162 =


target = sh4-linux
appsdir = ./
hostprefix = $(duckbox_path)/tdt/tufsbox/host
targetprefix = $(duckbox_path)/tdt/tufsbox/cdkroot
driverdir = $(duckbox_path)/tdt/cvs/driver
export BUILDPREFIX = $(duckbox_path)/tdt/cvs/cdk
buildprefix = $(duckbox_path)/tdt/cvs/cdk
KERNEL_DIR = linux-sh4
crossprefix = $(duckbox_path)/tdt/tufsbox/devkit/sh4


PATH := $(hostprefix)/ccache-bin:$(crossprefix)/bin:$(PATH):/usr/sbin

ifndef TOPDIR
TOPDIR=$(CURDIR)/
endif

all: do_compile

$(appsdir)/build/config.status:
	cd $(appsdir)/build && \
		./autogen.sh && \
		sed -e 's|#!/usr/bin/python|#!$(crossprefix)/bin/python|' -i xml2po.py && \
		./configure \
			--target=$(target) \
			--host=$(target) \
			--without-libsdl \
			--with-datadir=/usr/share \
			--with-libdir=/usr/lib \
			--with-plugindir=/usr/lib/tuxbox/plugins \
			--prefix=/usr \
			--sysconfdir=/etc \
			STAGING_INCDIR=$(hostprefix)/usr/include \
			STAGING_LIBDIR=$(hostprefix)/usr/lib \
			PKG_CONFIG=$(hostprefix)/bin/pkg-config \
			PKG_CONFIG_SYSROOT_DIR=$(targetprefix) \
			PKG_CONFIG_LIBDIR=$(targetprefix)/usr/lib/pkgconfig \
			PY_PATH=$(targetprefix)/usr \
			$(if $(CUBEREVO),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_CUBEREVO -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-cuberevo) \
			$(if $(CUBEREVO_MINI),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_CUBEREVO_MINI -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-cuberevo) \
			$(if $(CUBEREVO_MINI2),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_CUBEREVO_MINI2 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-cuberevo) \
			$(if $(CUBEREVO_MINI_FTA),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_CUBEREVO_MINI_FTA -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-cuberevo) \
			$(if $(CUBEREVO_250HD),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_CUBEREVO_250HD -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-cuberevo) \
			$(if $(CUBEREVO_2000HD),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_CUBEREVO_2000HD -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-cuberevo) \
			$(if $(CUBEREVO_9500HD),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_CUBEREVO_9500HD -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-cuberevo) \
			$(if $(UFS910),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_UFS910 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include") \
			$(if $(UFS922),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_UFS922 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include") \
			$(if $(TF7700),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_TF7700 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-tf7700) \
			$(if $(FLASH_UFS910),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_FLASH_UFS910 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include") \
			$(if $(FORTIS_HDBOX),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_FORTIS_HDBOX -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include") \
			$(if $(ATEVIO7500),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_ATEVIO7500 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include") \
			$(if $(HL101),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_HL101 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-hl101) \
			$(if $(VIP1_V2),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_VIP1_V2 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-vip1_v2) \
			$(if $(VIP2_V1),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_VIP2_V1 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include" --enable-vip2_v1) \
			$(if $(OCTAGON1008),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_OCTAGON1008 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include") \
			$(if $(UFS912),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_UFS912 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include") \
			$(if $(SPARK),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_SPARK -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include")  \
			$(if $(SPARK7162),CPPFLAGS="$(CPPFLAGS) -DPLATFORM_SPARK7162 -I$(driverdir)/include -I $(buildprefix)/$(KERNEL_DIR)/include")

do_compile: build/config.status
		cd $(appsdir)/build && \
		$(MAKE) all

distclean:
	cd $(appsdir)/build && \
	$(MAKE) distclean

install: do_compile
	cd $(appsdir)/build && \
	$(MAKE) install DESTDIR=$(TOPDIR)/staging

uninstall:
	cd $(appsdir)/build && \
	$(MAKE) uninstall

buildpkg: buildpkg-clean install
	cd $(TOPDIR); \
	if ! test -d packages; \
		then mkdir packages; fi; \
	dpkg-deb -b staging packages;
	cd packages; \
	for file in `ls |grep deb`; do \
		mv $$file `echo $$file |sed s/deb/ipk/`; \
	done

buildpkg-clean:
	cd $(TOPDIR)
	rm -rf staging

version:
	./version-bb.sh