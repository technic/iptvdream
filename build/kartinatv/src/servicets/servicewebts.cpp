
/*******************************************************************************
 VLC Player Plugin by A. Lätsch 2007

 Modified by Dr. Best
 Modified by technic
 	-KartinaTV & RodnoeTV compatibility
 	-Ring buffer now!!

 This is free software; you can redistribute it and/or modify it under
 the terms of the GNU General Public License as published by the Free
 Software Foundation; either version 2, or (at your option) any later
 version.
********************************************************************************/

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string>
#include <sys/socket.h>
#include <netdb.h>
#include <signal.h>
#include <time.h>
#include "servicewebts.h"
#include <lib/base/eerror.h>
#include <lib/base/object.h>
#include <lib/base/ebase.h>
#include <lib/service/service.h>
#include <lib/base/init_num.h>
#include <lib/base/init.h>
#include <lib/dvb/decoder.h>

#include <lib/base/nconfig.h> // access to python config

#include <lib/dvb/pmt.h>

#define MAX(a,b) ((a) > (b) ? (a) : (b))
#define MIN(a,b) ((a) < (b) ? (a) : (b))

int VPID = 0;
int PID_SET = 0;
int APID = 0;
int H264=0;


/********************************************************************/
/* eServiceFactoryWebTS                                                */
/********************************************************************/

eServiceFactoryWebTS::eServiceFactoryWebTS()
{
	ePtr<eServiceCenter> sc;

	eServiceCenter::getPrivInstance(sc);
	if (sc)
	{
		std::list<std::string> extensions;
		sc->addServiceFactory(eServiceFactoryWebTS::id, this, extensions);
	}
}

eServiceFactoryWebTS::~eServiceFactoryWebTS()
{
	ePtr<eServiceCenter> sc;

	eServiceCenter::getPrivInstance(sc);
	if (sc)
		sc->removeServiceFactory(eServiceFactoryWebTS::id);
}

DEFINE_REF(eServiceFactoryWebTS)

// iServiceHandler
RESULT eServiceFactoryWebTS::play(const eServiceReference &ref, ePtr<iPlayableService> &ptr)
{
	ptr = new eServiceTS(ref);
	return 0;
}

RESULT eServiceFactoryWebTS::record(const eServiceReference &ref, ePtr<iRecordableService> &ptr)
{
	ptr=0;
	return -1;
}

RESULT eServiceFactoryWebTS::list(const eServiceReference &, ePtr<iListableService> &ptr)
{
	ptr=0;
	return -1;
}

RESULT eServiceFactoryWebTS::info(const eServiceReference &ref, ePtr<iStaticServiceInformation> &ptr)
{
	ptr = 0;
	return -1;
}

RESULT eServiceFactoryWebTS::offlineOperations(const eServiceReference &, ePtr<iServiceOfflineOperations> &ptr)
{
	ptr = 0;
	return -1;
}


/********************************************************************/
/* TSAudioInfoWeb                                            */
/********************************************************************/
DEFINE_REF(TSAudioInfoWeb);

void TSAudioInfoWeb::addAudio(int pid, std::string lang, std::string desc, int type) {
	StreamInfo as;
	as.description = desc;
	as.language = lang;
	as.pid = pid;
	as.type = type;
	audioStreams.push_back(as);
}


/********************************************************************/
/* eServiceTS                                                       */
/********************************************************************/

eServiceTS::eServiceTS(const eServiceReference &url): m_pump(eApp, 1)
{
	eDebug("ServiceTS construct!");
	m_reference = url;
	m_filename = url.path.c_str();
	m_audioInfo = 0;
	m_destfd = -1;
	
	m_buffer_time = 0;
	std::string config_buftime;	
	if(ePythonConfigQuery::getConfigValue("config.plugins.KartinaTv.buftime", config_buftime) == 0)
		m_buffer_time = atoi(config_buftime.c_str());
	m_buffer_time = ((m_buffer_time < 12000) && (m_buffer_time > 100)) ? m_buffer_time : 2000;
}

eServiceTS::~eServiceTS()
{
	stop();
	eDebug("ServiceTS destruct!");
}

DEFINE_REF(eServiceTS);

size_t crop(char *buf)
{
	size_t len = strlen(buf) - 1;
	while (len > 0 && (buf[len] == '\r' || buf[len] == '\n')) {
		buf[len--] = '\0';
	}
	return len;
}

static int getline(char** pbuffer, size_t* pbufsize, int fd)
{
	size_t i = 0;
	int rc;
	while (true) {
		if (i >= *pbufsize) {
			char *newbuf = (char*)realloc(*pbuffer, (*pbufsize)+1024);
			if (newbuf == NULL)
				return -ENOMEM;
			*pbuffer = newbuf;
			*pbufsize = (*pbufsize)+1024;
		}
		rc = ::read(fd, (*pbuffer)+i, 1);
		if (rc <= 0 || (*pbuffer)[i] == '\n')
		{
			(*pbuffer)[i] = '\0';
			return rc <= 0 ? -1 : i;
		}
		if ((*pbuffer)[i] != '\r') i++;
	}
}



int eServiceTS::openHttpConnection(std::string url)
{
	std::string host;
	int port = 80;
	std::string uri;

	int slash = url.find("/", 7);
	if (slash > 0) {
		host = url.substr(7, slash-7);
		uri = url.substr(slash, url.length()-slash);
	} else {
		host = url.substr(7, url.length()-7);
		uri = "";
	}
	int dp = host.find(":");
	if (dp == 0) {
		port = atoi(host.substr(1, host.length()-1).c_str());
		host = "localhost";
	} else if (dp > 0) {
		port = atoi(host.substr(dp+1, host.length()-dp-1).c_str());
		host = host.substr(0, dp);
	}

	struct hostent* h = gethostbyname(host.c_str());
	if (h == NULL || h->h_addr_list == NULL)
		return -1;
	int fd = socket(PF_INET, SOCK_STREAM, 0);
	if (fd == -1)
		return -1;

	struct sockaddr_in addr;
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = *((in_addr_t*)h->h_addr_list[0]);
	addr.sin_port = htons(port);

	eDebug("connecting to %s:%d, %d", host.c_str(), port, time(0));

	if (connect(fd, (sockaddr*)&addr, sizeof(addr)) == -1) {
		std::string msg = "connect failed for: " + url;
		eDebug(msg.c_str());
		return -1;
	}
	eDebug("OK connected");
	std::string request = "GET ";
	request.append(uri).append(" HTTP/1.1\r\n");
	request.append("Host: ").append(host).append("\r\n");
	request.append("Accept: */*\r\n");
	request.append("Connection: Keep-Alive\r\n");
	request.append("\r\n");
	//eDebug(request.c_str());
	write(fd, request.c_str(), request.length());

	int rc;
	size_t buflen = 1000;
	char* linebuf = (char*)malloc(1000);

	rc = getline(&linebuf, &buflen, fd);
	eDebug("RECV(%d): %s", rc, linebuf);
	if (rc <= 0)
	{
		close(fd);
		free(linebuf);
		return -1;
	}

	char proto[100];
	int statuscode = 0;
	char statusmsg[100];
	rc = sscanf(linebuf, "%99s %d %99s", proto, &statuscode, statusmsg);
	if (rc < 2 || !((statuscode == 200) || (statuscode == 302)) ) {
		eDebug("wrong response: \"200 or 302\" expected.\n %d --- %d", rc, statuscode);
		free(linebuf);
		close(fd);
		return -1;
	} //Handle redirects!
	eDebug("proto=%s, code=%d, msg=%s", proto, statuscode, statusmsg);
	while (rc > 0)
	{
		rc = getline(&linebuf, &buflen, fd);
		eDebug("RECV(%d): %s", rc, linebuf);
		statuscode = sscanf(linebuf, "Location: %s", proto);
		if (statuscode == 1) {
			free(linebuf);
			std::string url(proto);
			return openHttpConnection(url);
		}
	}
	free(linebuf);

	return fd;
}

RESULT eServiceTS::connectEvent(const Slot2<void,iPlayableService*,int> &event, ePtr<eConnection> &connection)
{
	connection = new eConnection((iPlayableService*)this, m_event.connect(event));
	return 0;
}

RESULT eServiceTS::start()
{
	ePtr<eDVBResourceManager> rmgr;
	eDVBResourceManager::getInstance(rmgr);
	eDVBChannel dvbChannel(rmgr, 0);
	if (dvbChannel.getDemux(m_decodedemux, iDVBChannel::capDecode) != 0) {
		eDebug("Cannot allocate decode-demux");
		return -1;
	}
	if (m_decodedemux->getMPEGDecoder(m_decoder, 1) != 0) {
		eDebug("Cannot allocate MPEGDecoder");
		return -1;
	}
	if (m_destfd == -1)
	{
		char dvrDev[128];
		int dvrIndex = rmgr->m_adapter.begin()->getNumDemux() - 1;
		sprintf(dvrDev, "/dev/dvb/adapter0/dvr%d", dvrIndex);
		m_destfd = open(dvrDev, O_WRONLY);
		eDebug("open dvr device %99s", dvrDev);
	}
	//m_decoder->setVideoPID(m_vpid, eDVBVideo::MPEG2);
	//m_decoder->setAudioPID(m_apid, eDVBAudio::aMPEG);
	m_decoder->connectVideoEvent(slot(*this, &eServiceTS::video_event), m_video_event_connection);
	m_streamthread = new eStreamThread();
	CONNECT(m_streamthread->m_event, eServiceTS::recv_event);
	//m_decoder->freeze(0);
	//m_decoder->preroll();
	if (unpause() != 0)
		return -1;
	//m_event(this, evStart);
	return 0;
}

RESULT eServiceTS::stop()
{
	m_streamthread->stop();
	if (m_destfd >= 0)
	{
		::close(m_destfd);
		m_destfd = -1;
	}
	m_decodedemux->flush();
	m_audioInfo = 0;
	APID = 0;
	VPID = 0;
	PID_SET = 0;
	H264 = 0;
	printf("TS: %s stop\n", m_filename.c_str());
	return 0;
}

void eServiceTS::recv_event(int evt)
{
	eDebug("eServiceTS::recv_event: %d", evt);
	switch (evt) {
	case eStreamThread::evtEOS:
		m_decodedemux->flush();
		m_event((iPlayableService*)this, evEOF);
		break;
	case eStreamThread::evtReadError:
	case eStreamThread::evtWriteError:
		m_decoder->pause();
		m_event((iPlayableService*)this, evEOF);
		break;
	case eStreamThread::evtSOS:
		m_event((iPlayableService*)this, evSOF);
		break;
	case eStreamThread::evtStreamInfo:
		m_streamthread->getAudioInfo(m_audioInfo);
		if (PID_SET == 0 && APID != 0)
		{
			PID_SET = 1;
			m_decodedemux->flush();
			if (VPID != 0){
				if (H264)
					m_decoder->setVideoPID(VPID, eDVBVideo::MPEG4_H264);
				else
					m_decoder->setVideoPID(VPID, eDVBVideo::MPEG2);
			} else {
				std::string radio_pic;
				if (!ePythonConfigQuery::getConfigValue("config.misc.radiopic", radio_pic))
				m_decoder->setRadioPic(radio_pic);
			}
			//m_decoder->setAudioPID(APID, eDVBAudio::aMPEG);
			if (m_audioInfo) {
				eDebug("[ServiceTS] %d audiostreams found", m_audioInfo->audioStreams.size());
				selectTrack(0);
			}
			m_event(this, evStart);
			m_decoder->play();
			
		}
		break;
	}
}

void eServiceTS::video_event(struct iTSMPEGDecoder::videoEvent event)
{
	switch(event.type) {
		case iTSMPEGDecoder::videoEvent::eventSizeChanged:
			m_event((iPlayableService*)this, evVideoSizeChanged);
			break;
		case iTSMPEGDecoder::videoEvent::eventFrameRateChanged:
			m_event((iPlayableService*)this, evVideoFramerateChanged);
			break;
		case iTSMPEGDecoder::videoEvent::eventProgressiveChanged:
			m_event((iPlayableService*)this, evVideoProgressiveChanged);
			break;
		default:
			break;
	}
}

RESULT eServiceTS::pause(ePtr<iPauseableService> &ptr)
{
	ptr = this;
	return 0;
}

// iPausableService
RESULT eServiceTS::pause()
{
	m_streamthread->stop();
	m_decoder->pause();
	return 0;
}

RESULT eServiceTS::unpause()
{
	if (!m_streamthread->running())
	{
		int is_streaming = !strncmp(m_filename.c_str(), "http://", 7);
		int srcfd = -1;
		if (is_streaming){
			eDebug("We have http stream");
			srcfd = openHttpConnection(m_filename);
		}else
			srcfd = ::open(m_filename.c_str(), O_RDONLY);
		if (srcfd < 0) {
			eDebug("Cannot open source stream: %s", m_filename.c_str());
			return 1;
		}
		//m_decodedemux->flush();
		m_streamthread->start(srcfd, m_destfd, m_buffer_time);
		//m_decoder->unfreeze();
	}
	else
		eDebug("unpause but thread already running!");
	return 0;
}

//iStreamedService
RESULT eServiceTS::streamed(ePtr<iStreamedService> &ptr)
{
	ptr = this;
	return 0;
}

PyObject *eServiceTS::getBufferCharge()
{
	ePyObject tuple = PyTuple_New(0);
	return tuple;
}

int eServiceTS::setBufferSize(int size)
{
	m_buffer_time = size;
	return 0;
}

// iSeekableService
RESULT eServiceTS::seek(ePtr<iSeekableService> &ptr)
{
	ptr = this;
	return 0;
}

RESULT eServiceTS::getLength(pts_t &pts)
{
	return 0;
}

RESULT eServiceTS::seekTo(pts_t to)
{
	return 0;
}

RESULT eServiceTS::seekRelative(int direction, pts_t to)
{
	return 0;
}

RESULT eServiceTS::getPlayPosition(pts_t &pts)
{
	return 0;
}

RESULT eServiceTS::setTrickmode(int trick)
{
	return -1;
}

RESULT eServiceTS::isCurrentlySeekable()
{
	return 1;
}

RESULT eServiceTS::info(ePtr<iServiceInformation>&i)
{
	i = this;
	return 0;
}

RESULT eServiceTS::getName(std::string &name)
{
	name = m_filename;
	size_t n = name.rfind('/');
	if (n != std::string::npos)
		name = name.substr(n + 1);
	return 0;
}

int eServiceTS::getInfo(int w)
{
	switch (w)
	{
	case sVideoHeight:
		if (m_decoder)
			return m_decoder->getVideoHeight();
		break;
	case sVideoWidth:
		if (m_decoder)
			return m_decoder->getVideoWidth();
		break;
	case sFrameRate:
		if (m_decoder)
			return m_decoder->getVideoFrameRate();
		break;
	case sProgressive:
		if (m_decoder)
			return m_decoder->getVideoProgressive();
		break;
	case sAspect:
		if (m_decoder)
			return m_decoder->getVideoAspect();
		break;
	case sAudioPID:
		return m_apid;	
	case sVideoPID:
		if (VPID)
			return VPID;
	case sServiceref: return resIsString;
	case sProvider: return resIsString;
	default:
		break;
	}
	return -1;
}

std::string eServiceTS::getInfoString(int w)
{
	switch (w)
	{
	case sProvider:
		return "IPTV";
	case sServiceref:
		return m_reference.toString();
	default:
		break;
	}
	return iServiceInformation::getInfoString(w);

}

int eServiceTS::getNumberOfTracks() {
	if (m_audioInfo)
		return (int)m_audioInfo->audioStreams.size();
	else
		return 0;
}

RESULT eServiceTS::selectTrack(unsigned int i) {
	if (m_audioInfo) {
		m_apid = m_audioInfo->audioStreams[i].pid;
		eDebug("[ServiceTS] audio track %d PID 0x%02x type %d\n", i, m_apid, m_audioInfo->audioStreams[i].type);
		m_decoder->setAudioPID(m_apid, m_audioInfo->audioStreams[i].type);
		//m_decoder->set();
		m_event(this, evUpdatedInfo); //FIXME: hack for update audioInfo 
		return 0;
	} else {
		return -1;
	}
}

RESULT eServiceTS::getTrackInfo(struct iAudioTrackInfo &info, unsigned int n) {
	if (m_audioInfo) {
		info.m_pid = m_audioInfo->audioStreams[n].pid;
		info.m_description = m_audioInfo->audioStreams[n].description;
		info.m_language = m_audioInfo->audioStreams[n].language;
		return 0;
	} else {
		return -1;
	}
}

int eServiceTS::getCurrentTrack() {
	if (m_audioInfo) {
		for (size_t i = 0; i < m_audioInfo->audioStreams.size(); i++) {
			if (m_apid == m_audioInfo->audioStreams[i].pid) {
				return i;
			}
		}
	}
	return -1;
}

/********************************************************************/
/* eStreamThread                                                       */
/********************************************************************/

DEFINE_REF(eStreamThread)

eStreamThread::eStreamThread(): m_messagepump(eApp, 0) {
	CONNECT(m_messagepump.recv_msg, eStreamThread::recvEvent);
	m_running = false;
}

eStreamThread::~eStreamThread() {
}

void eStreamThread::start(int srcfd, int destfd, int buftime) {
	m_srcfd = srcfd;
	m_destfd = destfd;
	m_buffer_time = buftime;
	pthread_mutex_init(&m_mutex, NULL);
	pthread_cond_init(&m_full, NULL);
	m_stop = false;
	m_audioInfo = 0;
	run(IOPRIO_CLASS_RT);
}

void eStreamThread::stop() {
	m_stop = true;
	if(m_running) {
		//XXX: EDEBUG HERE HANG UP DREAMBOX, IF PYTHON CRASH OCCURES
		//TODO: REPORRT ENIGMA2 DEVELOPERS!!!
		//eDebug
		
		//mutex lock
		pthread_mutex_lock(&m_mutex);
		m_stop = true;
		pthread_cond_signal(&m_full);
		pthread_mutex_unlock(&m_mutex);
		//mutex unlock
	}
	kill();
}

void eStreamThread::recvEvent(const int &evt)
{
	m_event(evt);
}

RESULT eStreamThread::getAudioInfo(ePtr<TSAudioInfoWeb> &ptr)
{
	ptr = m_audioInfo;
	return 0;
}

#define REGISTRATION_DESCRIPTOR 5
#define LANGUAGE_DESCRIPTOR 10

std::string eStreamThread::getDescriptor(unsigned char buf[], int buflen, int type)
{
	int desc_len;
	while (buflen > 1) {
		desc_len = buf[1];
		if (buf[0] == type) {
			char str[21];
			if (desc_len > 20) desc_len = 20;
			strncpy(str, (char*)buf+2, desc_len);
			str[desc_len] = '\0';
			return std::string(str);
		} else {
			buflen -= desc_len+2;
			buf += desc_len+2;
		}
	}
	return "";
}

bool eStreamThread::scanAudioInfo(unsigned char buf[], int len)
{
	if (len < 1880)
		return false;

	int adaptfield, pmtpid, offset;
	unsigned char pmt[1188];
	int pmtsize = 0;

	for (int a=0; a < len - 188*4; a++) {
		if ( buf[a] != 0x47 || buf[a + 188] != 0x47 || buf[a + 376] != 0x47 )
			continue; // TS Header

		if ((0x40 & buf[a + 1]) == 0) // start
			continue;

		if ((0xC0 & buf[a + 3]) != 0) // scrambling
			continue;

		adaptfield = (0x30 & buf[a + 3]) >> 4;

		if ((adaptfield & 1) == 0) // adapt - no payload
			continue;

		offset = adaptfield == 3 ? 1 + (0xFF & buf[a + 4]) : 0; //adaptlength

		if (buf[a + offset + 4] != 0 || buf[a + offset + 5] != 2 || (0xF0 & buf[a + offset + 6]) != 0xB0)
		{
			a += 187;
			continue;
		}

		pmtpid = (0x1F & buf[a + 1])<<8 | (0xFF & buf[a + 2]);
		memcpy(pmt + pmtsize, buf + a + 4 + offset, 184 - offset);
		pmtsize += 184 - offset;

		if (pmtsize >= 1000)
			break;
	}

	if (pmtsize == 0) return false;

	int pmtlen = (0x0F & pmt[2]) << 8 | (0xFF & pmt[3]);
	std::string lang;
	std::string pd_type;
	ePtr<TSAudioInfoWeb> ainfo = new TSAudioInfoWeb();

	for (int b=8; b < pmtlen-4 && b < pmtsize-6; b++)
	{
		if ( (0xe0 & pmt[b+1]) != 0xe0 )
			continue;

		int pid = (0x1F & pmt[b+1])<<8 | (0xFF & pmt[b+2]);
		switch(pmt[b])
		{
		case 1:
		case 2: // MPEG Video
			//addVideo(pid, "MPEG2");
			H264 = 0;
			if (VPID == 0)
				VPID= pid;
			break;

		case 0x1B: // H.264 Video
			//addVideo(pid, "H.264");
			H264 = 1;
			if (VPID == 0)
				VPID= pid;
			break;
		case 3:
		case 4: // MPEG Audio
			if (APID == 0)
				APID =pid;
			lang = getDescriptor(pmt+b+5, pmt[b+4], LANGUAGE_DESCRIPTOR);
			ainfo->addAudio(pid, lang, "MPEG", eDVBAudio::aMPEG);
			//printf("addAudio %d MPEG", pid);
			break;

		case 0x80:
		case 0x81:  //private data of AC3 in ATSC
			//also found that it could be ac-3 pid:) for example rodnoe.tv
			lang = getDescriptor(pmt+b+5, pmt[b+4], LANGUAGE_DESCRIPTOR);
			pd_type = getDescriptor(pmt+b+5, pmt[b+4], REGISTRATION_DESCRIPTOR);
			//if (pd_type == "AC-3")
			// dirty dirty :-) Aber es funktioniert...
			//if (lang.length() != 0)
			//{
				ainfo->addAudio(pid, lang, "AC3", eDVBAudio::aAC3);
				if (APID == 0)
					APID =pid;
			//}
			break;
		case 0x82:
		case 0x83:
		case 6:
			lang = getDescriptor(pmt+b+5, pmt[b+4], LANGUAGE_DESCRIPTOR);
			pd_type = getDescriptor(pmt+b+5, pmt[b+4], REGISTRATION_DESCRIPTOR);
			//if (pd_type == "AC-3")
			// dirty dirty :-) Aber es funktioniert...
			//if (lang.length() != 0)
			//{
				ainfo->addAudio(pid, lang, "AC3", eDVBAudio::aAC3);
				if (APID == 0)
					APID =pid;
			//}
			break;
		case 0x0F:  // MPEG 2 AAC
			if (APID == 0)
				APID =pid;
			lang = getDescriptor(pmt+b+5, pmt[b+4], LANGUAGE_DESCRIPTOR);	
			ainfo->addAudio(pid, lang, "AAC", eDVBAudio::aAAC);
			//printf("addAudio %d AAC", pid);
		}
		b += 4 + pmt[b+4];
	}
	if (ainfo->audioStreams.size() > 0) {
		m_audioInfo = ainfo;
		return true;
	} else {
		return false;
	}
}

void eStreamThread::thread() {
	const int bufsize = 1 << 22; //4 MB TODO: define
	//const int bufmask = bufsize -1;
	const int blocksize = 15000;
	int rc, avail, put, get, size;
	time_t next_scantime = 0;
	fd_set wset;
	bool sosSend = false;
	bool stop = false;
	int predone = 15000;
	struct RingBuffer ring; 
	
	m_running = true;
	
	unsigned char* buf = (unsigned char*) malloc(bufsize);
	if (buf == NULL) {
		eDebug("eStreamThread malloc ERROR");
		return;
	}

	eDebug("eStreamThread started with buffering time = %d ms", m_buffer_time);
	ring.put = 1;
	ring.get = 0;
	ring.size = bufsize;
	ring.stop = false;
		
	pthread_cond_t empty;
	pthread_cond_init(&empty, NULL);
	
	eStreamThreadPut *putThread = new eStreamThreadPut();
	putThread->start(m_srcfd, buf, &ring, &m_mutex, &empty, &m_full);
	
	hasStarted();
	//wait for prebuffering
	usleep(1000*m_buffer_time);
	
	while (!m_stop) {
		pthread_testcancel();
		
		//start wait for event
		pthread_mutex_lock(&m_mutex);
		do {
			put = ring.put;
			get = ring.get;
			size = ring.size;
			stop = ring.stop;
		
			if (get > put) {
				avail = size - get;
				if(put == 0) avail--;
			} else {
				avail = put - get - 1;
			}
			if(stop) { 
				break; //putThread ended, but we should write all data from buffer
			}
			if(avail <= predone) {
				//eDebug("eStreamThread wating for signal. Avail = %d", avail);
				pthread_cond_wait(&m_full, &m_mutex);
			}
			if(m_stop){
				eDebug("eStreamThread stop immediately");
			}	
		} while(avail <= predone && !m_stop && !stop);
		pthread_mutex_unlock(&m_mutex);
		//event occured
		if (m_stop) { //global stop quit immediately
			eDebug("eStreamThread catch stop signal");
			break;
		}
		
		if(stop && avail <= predone)
			break;
		
		if (avail > predone && predone != 0)
		{
			predone = 0;
			eDebug("eStreamThread prebuffering DONE %d", time(0));
		}
			
		FD_ZERO(&wset);
		FD_SET(m_destfd, &wset);
		struct timeval timeout;
		int maxfd;
		timeout.tv_sec = 1;
		timeout.tv_usec = 0;
		maxfd = m_destfd + 1;
		
		rc = select(maxfd, NULL, &wset, NULL, &timeout);
		if (rc < 0) {
			eDebug("eStreamThreadGet error in select (%d)", errno);
			break;
		}
		if (rc == 0) {
			eDebug("eStreamThreadGet timeout!");
			continue;
		}
			
		rc = ::write(m_destfd, buf+get, MIN(avail, blocksize));
		//eDebug("eStreamThreadGet write=%d", rc);
		if (rc < 0) {
			eDebug("eStreamThreadGet error in write (%d)", errno);
			m_messagepump.send(evtWriteError);
			break;
		}
			
		if (!sosSend) {
			m_messagepump.send(evtSOS);
			sosSend = true;
		}
		if (time(0) >= next_scantime && (get+rc) >= blocksize) {
			if (scanAudioInfo(buf+get+rc-blocksize, blocksize)) {
				m_messagepump.send(evtStreamInfo);
				next_scantime = time(0) + 1;
			}
		}
		//mutex lock
		pthread_mutex_lock(&m_mutex);
		ring.get = (ring.get + rc) & (ring.size-1);
		pthread_cond_signal(&empty);
		pthread_mutex_unlock(&m_mutex);
		//mutex unlock
	}
	
	m_messagepump.send(evtEOS);
	//mutex lock
	pthread_mutex_lock(&m_mutex);
	ring.stop = true;
	eDebug("eStreamThread send stop signal");
	pthread_cond_signal(&empty);
	pthread_mutex_unlock(&m_mutex);
	//mutex unlock
	
	putThread->stop();
	free(buf);
	eDebug("eStreamThread end");
}

void eStreamThread::thread_finished() {
	if (m_srcfd >= 0)
		::close(m_srcfd);
	eDebug("eStreamThread closed");
	m_running = false;
}



/********************************************************************/
/*                    eStreamThreadPut                              */
/********************************************************************/

DEFINE_REF(eStreamThreadPut)

eStreamThreadPut::eStreamThreadPut()
{
	m_running = false;
}

eStreamThreadPut::~eStreamThreadPut() {
}

void eStreamThreadPut::start(int srcfd, unsigned char *buffer, struct RingBuffer *ring, pthread_mutex_t *mutex, pthread_cond_t *empty, pthread_cond_t *full)
{
	m_srcfd = srcfd;
	m_buf = buffer;
	m_ring = ring;
	m_mutex = mutex;
	m_empty = empty;
	m_full = full;
	m_stop = false;
	run(IOPRIO_CLASS_RT);
}

void eStreamThreadPut::stop() {
	m_stop = true;
	kill();
}

void eStreamThreadPut::thread()
{
	int free, size, get, put, rc;
	int packsize = 10000;
	fd_set rset;
	struct timeval timeout;
	bool stop = false;
	int timeouts = 0;

	hasStarted();
	eDebug("eStreamThreadPut started");
	
	while (!m_stop) {
		pthread_testcancel();
		
		//wait for event
		do{
			put = m_ring->put;
			get = m_ring->get;
			size = m_ring->size;
			stop = m_ring->stop;
			if(stop) break;
			if (put > get) {
				free = size - put;
				if(get == 0) free--;
			} else {
				free = get - put - 1 - 15000;
			}
			//eDebug("eStreamThreadPut free = %d", free);
			if(free <= 0) {
				eDebug("eStreamThreadPut buffer full");
				pthread_cond_wait(m_empty, m_mutex);
			}
		} while(free <= 0 && !m_stop);
		pthread_mutex_unlock(m_mutex);
		//event occured
		if(stop)
			break;
		
		//start reading
		int maxfd = 0;
		FD_ZERO(&rset);
		FD_SET(m_srcfd, &rset);
		timeout.tv_sec = 1;
		timeout.tv_usec = 500*1000;
		maxfd = m_srcfd + 1;
		rc = select(maxfd, &rset, NULL, NULL, &timeout);
		if (rc < 0) {
			eDebug("eStreamThreadPut error in select (%d)", errno);
			break;
		}
		if (rc == 0) {
			eDebug("eStreamThreadPut timeout!");
			timeouts += 1;
			if(timeouts > 10){
				eDebug("more than 10 timeouts. close");
				break;
			}
			continue;
		}			
		
		if(timeouts > 0){
			timeouts = 0;
			eDebug("reset timeout counter");
		}
		
		rc = ::read(m_srcfd, m_buf+put, MIN(free, packsize) );
		
		//eDebug("eStreamThreadPut read %d", rc);
		
		if(rc < 0){
			eDebug("eStreamThreadPut read error (%d)", errno);
			break;
		} else if (rc == 0) {
			eDebug("eStreamThreadPut EOF");
			break;
		} else {
			//mutex lock
			pthread_mutex_lock(m_mutex);
			m_ring->put = (put+rc) & (m_ring->size-1);
			//eDebug("eStreamThreadPut send signal, put = %d", m_ring->put);
			pthread_cond_signal(m_full);
			pthread_mutex_unlock(m_mutex);
			//mutex unlock				
		}
		
	}
	eDebug("eStreamThreadPut loop stopped");
	//mutex lock
	pthread_mutex_lock(m_mutex);
	m_ring->stop = true;  //notify writeThread that we stopped
	pthread_cond_signal(m_full);
	pthread_mutex_unlock(m_mutex);
	//mutex unlock	
	eDebug("eStreamThreadPut end");
}

void eStreamThreadPut::thread_finished() {
	if (m_srcfd >= 0)
		::close(m_srcfd);
	eDebug("eStreamThreadPut closed");
	m_running = false;
}


eAutoInitPtr<eServiceFactoryWebTS> init_eServiceFactoryWebTS(eAutoInitNumbers::service+1, "eServiceFactoryWebTS");

PyMODINIT_FUNC
initservicewebts(void)
{
	Py_InitModule("servicewebts", NULL);
}
