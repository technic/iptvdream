// Written by Dmitry <a7051999@mail.ru>
// Written by Alex Maystrenko <alexeytech@gmail.com>
//

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>

#include <iostream>
using namespace std;

#include <Python.h>

#define error(test,str) if(test){printf(str);return 1;}

#define WINUNIX_FACTOR 10000000
#define WINUNIX_DIFF 11644473600LL
#define MOSCOW_TIME 14400

static PyObject *
jtvread_curr(PyObject *self, PyObject *args)
{
	static char *fname;
	if (!PyArg_ParseTuple(args, "s", &fname))
		return NULL;

	int f2,f3;
	char name[5000];
	
	char sf2[150];
	sprintf(sf2, "%s.ndx", fname);
	char sf3[150];
	sprintf(sf3, "%s.pdt", fname);
	
	f2 = open(sf2, O_RDONLY);
	if (f2 < 0) {
		cout << "Can't open file " << sf2 << " errno" << errno << endl;
		return PyErr_SetFromErrno(PyExc_IOError);
	}
	f3 = open(sf3, O_RDONLY);
	if (f3 < 0) {
		cout << "Can't open file " << sf3 << " errno" << errno << endl;
		return PyErr_SetFromErrno(PyExc_IOError);
	}

	int nelem=0;
	if (read(f2, &nelem, 2) < 0) {
		cout << "Read error!\n";
		return PyErr_SetFromErrno(PyExc_IOError);
	}
	
	time_t t = time(0);
//     struct tm* data;
//     data = localtime(&t);
//     data->tm_isdst = 0;
//     time_t t1 = mktime(data);
//     data = gmtime(&t);
//     data->tm_isdst = 0;
//     time_t t2 = mktime(data);
//     int gmtoffset = (t1 - t2);
	long now = t + MOSCOW_TIME;
//	printf("tz %d\n", gmtoffset);

	int a = 0;
	int b = nelem-1;
	int pos;
	while(b-a > 1) {
		pos = a + (b-a)/2;
		lseek(f2, 2+pos*12, SEEK_SET);
		
// 		cout << a << endl;
// 		cout << pos << endl;
// 		cout << b << endl;
		
		int tmp;
		long long ft;
		read(f2,&tmp,2);
		read(f2,&ft,8);
	
		long ftsec;
		ftsec = ft / WINUNIX_FACTOR - WINUNIX_DIFF;
		
// 		cout << ftsec << endl;

		if(ftsec >= now){
			b = pos;
		} else {
			a = pos;
		}
	}
	pos = a+(b-a)/2;
	
	//cout << "all " << nelem << endl;
	//cout << "found " << now << " at " << pos << endl;
	
	lseek(f2, 2+pos*12, SEEK_SET);
	const int max = 3;
	int count = max;
	if(pos+max > nelem)
		count = nelem-pos;
	
	PyObject* epglist = PyTuple_New(count);
	
	for(int i = pos; i < nelem && i < pos+max; i++){
		
		int tmp;
		long long ft;
		read(f2,&tmp,2);
		read(f2,&ft,8);
		
		long ftsec;
		ftsec = ft / WINUNIX_FACTOR - WINUNIX_DIFF;
		
		long offset=0;
		read(f2,&offset,2);
		lseek(f3,offset,SEEK_SET);
		int len=0;
		read(f3,&len,2);
		read(f3,name,len);name[len]=0;

		PyObject* entry = PyTuple_New(2);
		PyTuple_SetItem(entry, 0, PyInt_FromLong(ftsec));
		PyObject* py_string = PyString_FromString(name);
		if (!py_string) {
			PyErr_Print();
		}
		PyObject* qq = PyString_AsDecodedObject(py_string, "cp1251", NULL);
		Py_DECREF(py_string);
		PyTuple_SetItem(entry, 1, qq);
		PyTuple_SetItem(epglist, i-pos, entry);
	}

	close(f2);
	close(f3);
	
	return epglist;
}

static PyObject *
jtvread(PyObject *self, PyObject *args)
{
	static char *fname;
	if (!PyArg_ParseTuple(args, "s", &fname))
		return NULL;

	int f2,f3;
	char name[5000];
	
	char sf2[150];
	sprintf(sf2, "%s.ndx", fname);
	char sf3[150];
	sprintf(sf3, "%s.pdt", fname);
	
	f2 = open(sf2, O_RDONLY);
	if (f2 < 0) {
		cout << "Can't open file " << sf2 << " errno" << errno << endl;
		return PyErr_SetFromErrno(PyExc_IOError);
	}
	f3 = open(sf3, O_RDONLY);
	if (f3 < 0) {
		cout << "Can't open file " << sf3 << " errno" << errno << endl;
		return PyErr_SetFromErrno(PyExc_IOError);
	}

	int nelem=0;
	if (read(f2, &nelem, 2) < 0) {
		cout << "Read error!\n";
		return PyErr_SetFromErrno(PyExc_IOError);
	}
	
	PyObject* epglist = PyTuple_New(nelem);
	
	//while(
	
	for(int i=0;i<nelem;i++){
		int tmp;
		long long ft;
		read(f2,&tmp,2);
		read(f2,&ft,8);
		
		long ftsec;
		ftsec = ft / WINUNIX_FACTOR - WINUNIX_DIFF;

		long offset=0;
		read(f2,&offset,2);
		lseek(f3,offset,SEEK_SET);
		int len=0;
		read(f3,&len,2);
		read(f3,name,len);name[len]=0;

		PyObject* entry = PyTuple_New(2);
		PyTuple_SetItem(entry, 0, PyInt_FromLong(ftsec));
		PyObject* py_string = PyString_FromString(name);
		if (!py_string) {
			PyErr_Print();
		}
		PyObject* qq = PyString_AsDecodedObject(py_string, "cp1251", NULL);
		Py_DECREF(py_string);
		PyTuple_SetItem(entry, 1, qq);
		PyTuple_SetItem(epglist, i, entry);
	}

	close(f2);
	close(f3);
	
	return epglist;
}

static PyMethodDef jtvreadMethods[] = {
	{"read",  jtvread, METH_VARARGS, "Return epg tuples from ndx+pdt files. Usage jtvreader.read(channel_name)."},
	{"current",  jtvread_curr, METH_VARARGS, "Return epg tuples from ndx+pdt files. Usage jtvreader.read(channel_name)."},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initjtvreader(void)
{
	(void) Py_InitModule("jtvreader", jtvreadMethods);
}
