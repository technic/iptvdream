/*******************************************************************************
 VLC Player Plugin by A. Lätsch 2007

 This is free software; you can redistribute it and/or modify it under
 the terms of the GNU General Public License as published by the Free
 Software Foundation; either version 2, or (at your option) any later
 version.
********************************************************************************/

#ifndef __servicewebts_h
#define __servicewebts_h

#include <lib/base/ioprio.h>
#include <lib/base/message.h>
#include <lib/service/iservice.h>
#include <lib/dvb/dvb.h>



#define PRIVATE_STREAM1  0xBD
#define PRIVATE_STREAM2  0xBF

#define AUDIO_STREAM_S   0xC0
#define AUDIO_STREAM_E   0xDF

#define VIDEO_STREAM_S   0xE0
#define VIDEO_STREAM_E   0xEF

#define TS_SIZE          188
#define IN_SIZE		 65424

#define PID_MASK_HI      0x1F







class eStaticServiceWebTSInfo;

class eServiceFactoryWebTS: public iServiceHandler
{
DECLARE_REF(eServiceFactoryWebTS);
public:
	eServiceFactoryWebTS();
	virtual ~eServiceFactoryWebTS();
	enum { id = 0x1010 };

	// iServiceHandler
	RESULT play(const eServiceReference &, ePtr<iPlayableService> &ptr);
	RESULT record(const eServiceReference &, ePtr<iRecordableService> &ptr);
	RESULT list(const eServiceReference &, ePtr<iListableService> &ptr);
	RESULT info(const eServiceReference &, ePtr<iStaticServiceInformation> &ptr);
	RESULT offlineOperations(const eServiceReference &, ePtr<iServiceOfflineOperations> &ptr);
};

class TSAudioInfoWeb {
DECLARE_REF(TSAudioInfoWeb);
public:
	struct StreamInfo {
		int pid;
		int type;
		std::string language; /* iso639 */
		std::string description;
	};
	std::vector<StreamInfo> audioStreams;
	void addAudio(int pid, std::string lang, std::string desc, int type);
};


class eStreamThread;
class eServiceTS: public iPlayableService, public iPauseableService,
	public iServiceInformation, public iSeekableService,
	public iAudioTrackSelection, public iAudioChannelSelection, public Object
{
DECLARE_REF(eServiceTS);
public:
	virtual ~eServiceTS();

	// iPlayableService
	RESULT connectEvent(const Slot2<void,iPlayableService*,int> &event, ePtr<eConnection> &connection);
	RESULT start();
	RESULT stop();
	RESULT pause(ePtr<iPauseableService> &ptr);
	RESULT seek(ePtr<iSeekableService> &ptr);
	RESULT info(ePtr<iServiceInformation>&);

	// not implemented
	RESULT setTarget(int target) { return -1; };
	RESULT setSlowMotion(int ratio) { return -1; };
	RESULT setFastForward(int ratio) { return -1; };
	RESULT audioChannel(ePtr<iAudioChannelSelection> &ptr) { ptr = this; return 0; };
	RESULT audioTracks(ePtr<iAudioTrackSelection> &ptr) { ptr = this; return 0; };
	RESULT frontendInfo(ePtr<iFrontendInformation> &ptr) { ptr = 0; return -1; };
	RESULT subServices(ePtr<iSubserviceList> &ptr) { ptr = 0; return -1; };
	RESULT timeshift(ePtr<iTimeshiftService> &ptr) { ptr = 0; return -1; };
	RESULT cueSheet(ePtr<iCueSheet> &ptr) { ptr = 0; return -1; };
	RESULT subtitle(ePtr<iSubtitleOutput> &ptr) { ptr = 0; return -1; };
	RESULT audioDelay(ePtr<iAudioDelay> &ptr) { ptr = 0; return -1; };
	RESULT rdsDecoder(ePtr<iRdsDecoder> &ptr) { ptr = 0; return -1; };
	RESULT stream(ePtr<iStreamableService> &ptr) { ptr = 0; return -1; };
	RESULT keys(ePtr<iServiceKeys> &ptr) { ptr = 0; return -1; };

	// iPausableService
	RESULT pause();
	RESULT unpause();


	// iSeekableService
	RESULT getLength(pts_t &SWIG_OUTPUT);
	RESULT seekTo(pts_t to);
	RESULT seekRelative(int direction, pts_t to);
	RESULT getPlayPosition(pts_t &SWIG_OUTPUT);
	RESULT setTrickmode(int trick);
	RESULT isCurrentlySeekable();

	// iServiceInformation
	RESULT getName(std::string &name);
	int getInfo(int w);
	std::string getInfoString(int w);

	// iAudioTrackSelection
	int getNumberOfTracks();
	RESULT selectTrack(unsigned int i);
	SWIG_VOID(RESULT) getTrackInfo(struct iAudioTrackInfo &, unsigned int n);
	int getCurrentTrack();

	// iAudioChannelSelection
	int getCurrentChannel() { return iAudioChannelSelection_ENUMS::STEREO; };
	RESULT selectChannel(int i) { return 0; };

private:
	friend class eServiceFactoryWebTS;
	eServiceReference m_reference;
	std::string m_filename;
	int m_vpid, m_apid;
	int m_destfd;
	int m_buffer_time;
	ePtr<iDVBDemux> m_decodedemux;
	ePtr<iTSMPEGDecoder> m_decoder;
	ePtr<eStreamThread> m_streamthread;
	ePtr<TSAudioInfoWeb> m_audioInfo;

	eServiceTS(const eServiceReference &url);
	int openHttpConnection(std::string url);

	Signal2<void,iPlayableService*,int> m_event;
	eFixedMessagePump<int> m_pump;
	void recv_event(int evt);
	void setAudioPid(int pid, int type);
	
	ePtr<eConnection> m_video_event_connection;
	void video_event(struct iTSMPEGDecoder::videoEvent);
};

class eStreamThread: public eThread, public Object {
DECLARE_REF(eStreamThread);
public:
	eStreamThread();
	virtual ~eStreamThread();
	void start(int srcfd, int destfd, int buftime);
	void stop();
	bool running() { return m_running; }

	virtual void thread();
	virtual void thread_finished();

	RESULT getAudioInfo(ePtr<TSAudioInfoWeb> &ptr);

	enum { evtEOS, evtSOS, evtReadError, evtWriteError, evtUser, evtStreamInfo };
	Signal1<void,int> m_event;
private:
	bool m_stop;
	bool m_running;
	int m_srcfd, m_destfd, m_buffer_time;
	pthread_cond_t m_full;
	pthread_mutex_t m_mutex;
	ePtr<TSAudioInfoWeb> m_audioInfo;
	eFixedMessagePump<int> m_messagepump;
	void recvEvent(const int &evt);
	bool scanAudioInfo(unsigned char buf[], int len);
	std::string getDescriptor(unsigned char buf[], int buflen, int type);
};

class eStreamThreadPut: public eThread, public Object {
DECLARE_REF(eStreamThreadPut);
public:
	eStreamThreadPut();
	virtual ~eStreamThreadPut();
	void start(int srcfd, unsigned char *buffer, struct RingBuffer *ring, pthread_mutex_t *mutex, pthread_cond_t *empty, pthread_cond_t *full);
	void stop();
	bool running() { return m_running; }

	virtual void thread();
	virtual void thread_finished();

	RESULT getAudioInfo(ePtr<TSAudioInfoWeb> &ptr);

	enum { evtEOS, evtSOS, evtReadError, evtWriteError, evtUser, evtStreamInfo};
	Signal1<void,int> m_event;
private:
	bool m_stop;
	bool m_running;
	int m_srcfd;
	unsigned char *m_buf;
	struct RingBuffer *m_ring;
	pthread_mutex_t *m_mutex;
	pthread_cond_t *m_empty, *m_full;
};

struct RingBuffer {
	int put, get, size;
	bool stop;
};

#endif

