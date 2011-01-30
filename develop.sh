#!/bin/bash

place_src="usr/lib/enigma2/python/Plugins/Extensions/KartinaTV"
plug_path="/usr/lib/enigma2/python/Plugins/Extensions/"
build_path="staging"
snap_path="snapshots"
pack_path="packages"
export DESTDIR=`pwd`/staging


echo "Welcome to dreambox bulder v0.2 ! developed by technic(c)"
echo "Добро пожаловть в дримбокс билдер v0.2 ! Разработано technic(с)"


if [ -d $2 && -z $2 ]; then
  src=$2
else
  src="build"
fi

echo "find sources path: " $src

rename(){
  echo ""
  echo "rename packages"
  for file in `ls $pack_path |grep deb`; do
     mv $pack_path/$file $pack_path/`echo $file |sed s/deb/ipk/` -v
  done
}

buildpkg(){
    pack=`cat $build_path/DEBIAN/control |grep Package`
    ver=`cat $build_path/DEBIAN/control |grep Version`
    echo "Bulding $pack"
    echo "Current $ver"
    read -p "Enter new version: " newver
    sed "s/Version:.*/Version: $newver/" $build_path/DEBIAN/control > control.tmp
    mv control.tmp $build_path/DEBIAN/control
    if [ ! -d $pack_path ]; then
    	mkdir $pack_path
    fi
    dpkg-deb -b $build_path $pack_path
    rename
}

snapshot(){
    echo ""
    echo "doing snapshot..."
    if ! test -d $snap_path; then
    	mkdir $snap_path
    fi
    name="$snap_path/KartinaTV_`date +"%Y%m%d"`-r"
    n=0
    while [ -f "$name$n.tar.gz" ]; do
        n=`expr $n + 1`
    done
	clean
    echo "saving to $name$n.tar.gz"
    tar -czf $name$n.tar.gz $src
}

makeinstallsrc(){
	echo ""
	echo "clean build tree"
	rm -rv  $build_path/usr 
    echo ""
    echo "make install src"
    cd $src
    make
    make install
    if [ `echo $?` != 0 ]; then
    	echo ""
    	echo "make ERROR"
    	echo "Aborting..."
    	exit 2
    fi
    cd ..
}

makesrc(){
    echo ""
    echo "make src"
    cd $src
    echo $src
    make
    cd ..
}

putftp(){
 #files="plugin.py kartina.py servicewebts.so"
 #echo "Uploading files ( $files ) to dreambox"
 #for f in $files; do
 # wput ${src}src/$f ftp://root@192.168.0.178/$place_src/$f
 #done
 echo "wput -N $build_path/$place_src/* ftp://root@192.168.0.178/$place_src/ --basename=$build_path/$place_src/"
 wput -N $build_path/$place_src/* ftp://root@192.168.0.178/$place_src/ --basename=$build_path/$place_src/
}

reboot()
{
  echo ""
  echo "Upload done"
  read -p "Reboot your dreambox? [y/n]:" ans
  if [ $ans == "y" ]; then 
   echo "you say reboot";
   ./reboot-dream.py
  fi
}
clean()
{
    cd $src
    make clean
    cd ../
}

case "$1" in
    buildpkg)
     makeinstallsrc
     buildpkg
     
    ;;
    clean)
     clean
    ;;
    
    makesrc)
     makeinstallsrc
    ;;
    
    make)
     makesrc
    ;;
    
    ftp)
   	 makeinstallsrc
   	 putftp
   	 reboot
   	;;
    
    snap)
     snapshot   
    ;;
    
    *)
        echo "Usage: $0 [option] [srcpath]"
        echo "ftp"
        echo "makesrc"
        echo "buildpkg"
        echo "snap"
        echo "clean"
        echo "help"
    
esac
