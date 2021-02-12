/* diag_revealer.c
 * Read diagnostic message from Android's /dev/diag device. Messages are output
 * using a Linux FIFO pipe.
 *
 * Author: Jiayao Li, Yuanjie Li, Haotian Deng
 * Changes:
 *   Ruihan Li: Probe ioctl argument length.
 *              Fix libdiag.so logging switching.
 *              Add Android 10 support.
 */

/* This program writes to FIFO using a special packet format:
 *    type: 2-byte integer. Can be one of the following values:
 *      1: LOG
 *      2: START_LOG_FILE, indicating the creation of a new log file.
 *      3: END_LOG_FILE, indicating the end of a log file.
 *    length: 2-byte integer. The total number of bytes in this packet
 *      (excluding the type field).
 * If "type" is LOG, there are two other fields:
 *    timestamp: 8-byte double float number. A POSIX timestamp representing
 *      when this log is received from the device.
 *    payload: byte stream of variable length.
 * Otherwise, "type" contains only one field:
 *    filename: the related log file's name
 */

#include <assert.h>
#include <endian.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <sys/mman.h>
#include <dlfcn.h>

// #include <linux/diagchar.h>
#define _GNU_SOURCE
#define F_SETPIPE_SZ (F_LINUX_SPECIFIC_BASE + 7)
#define F_GETPIPE_SZ (F_LINUX_SPECIFIC_BASE + 8)
#include <fcntl.h>

#include <android/log.h>
#define  LOG_TAG    "diag_revealer"

#define  LOGE(...)  __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define  LOGW(...)  __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)
#define  LOGD(...)  __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)
#define  LOGI(...)  __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

typedef int (*D_FUNC)(int, int);
typedef signed int (*I_FUNC)();
typedef int (*F_FUNC)(int);
typedef int (*R_FUNC)(const char *);

// NOTE: the following number should be updated every time.
#define DIAG_REVEALER_VERSION "3.0"

#define LOG_CUT_SIZE_DEFAULT (1 * 1024 * 1024)
// #define BUFFER_SIZE	8192
// #define BUFFER_SIZE	32768
#define BUFFER_SIZE	65536
/*
 * size of FIFO pipe between diag_revealer and AndroidDiagMonitor
 */
// #define DIAG_FIFO_PIPE_SIZE (128 * 1024 * 1024) // 128MB
#define DIAG_FIFO_PIPE_SIZE (10 * 1024 * 1024) // 10MB

#define FIFO_MSG_TYPE_LOG 1
#define FIFO_MSG_TYPE_START_LOG_FILE 2
#define FIFO_MSG_TYPE_END_LOG_FILE 3

#define LIBDIAG_TMPPATH "/data/data/net.mobileinsight.app/cache/libdiag.so"

/*
 * MDM VS. MSM
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/include/linux/diagchar.h
 */
enum remote_procs {
	MSM = 0,
	MDM = 1,
	MDM2 = 2,
	QSC = 5,
};

/* Raw binary data type
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/include/linux/diagchar.h
 */
#define MSG_MASKS_TYPE		0x00000001
#define LOG_MASKS_TYPE		0x00000002
#define EVENT_MASKS_TYPE	0x00000004
#define PKT_TYPE		0x00000008
#define DEINIT_TYPE		0x00000010
#define USER_SPACE_DATA_TYPE	0x00000020
#define DCI_DATA_TYPE		0x00000040
#define CALLBACK_DATA_TYPE	0x00000080
#define DCI_LOG_MASKS_TYPE	0x00000100
#define DCI_EVENT_MASKS_TYPE	0x00000200
#define DCI_PKT_TYPE		0x00000400

/* IOCTL commands for diagnostic port
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/include/linux/diagchar.h
 */
#define DIAG_IOCTL_SWITCH_LOGGING	7
#define DIAG_IOCTL_LSM_DEINIT		9
#define DIAG_IOCTL_DCI_REG		23
#define DIAG_IOCTL_DCI_INIT		20
#define DIAG_IOCTL_DCI_DEINIT		21
#define DIAG_IOCTL_DCI_CLEAR_LOGS	28
#define DIAG_IOCTL_DCI_CLEAR_EVENTS	29
#define DIAG_IOCTL_REMOTE_DEV		32
#define DIAG_IOCTL_VOTE_REAL_TIME	33
#define DIAG_IOCTL_GET_REAL_TIME	34
#define DIAG_IOCTL_PERIPHERAL_BUF_CONFIG	35
#define DIAG_IOCTL_PERIPHERAL_BUF_DRAIN		36

#define MEMORY_DEVICE_MODE		2
#define CALLBACK_MODE			6
#define TTY_MODE			8

/*
 * NEXUS-6-ONLY IOCTL
 * Reference: https://github.com/MotorolaMobilityLLC/kernel-msm/blob/kitkat-4.4.4-release-victara/include/linux/diagchar.h
 */
#define DIAG_IOCTL_OPTIMIZED_LOGGING		35
#define DIAG_IOCTL_OPTIMIZED_LOGGING_FLUSH	36

/*
 * Buffering mode
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/include/linux/diagchar.h
 */
#define DIAG_BUFFERING_MODE_STREAMING	0
#define DIAG_BUFFERING_MODE_THRESHOLD	1
#define DIAG_BUFFERING_MODE_CIRCULAR	2
#define DEFAULT_LOW_WM_VAL	15
#define DEFAULT_HIGH_WM_VAL	85
#define NUM_SMD_DATA_CHANNELS	4
#define NUM_SMD_CONTROL_CHANNELS NUM_SMD_DATA_CHANNELS

#define MODEM_DATA		0
#define LAST_PERIPHERAL		3

/*
 * Structures for DCI client registration
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/drivers/char/diag/diag_dci.h
 */
#define DCI_LOG_MASK_SIZE		(16 * 514)
#define DCI_EVENT_MASK_SIZE		512
struct diag_dci_reg_tbl_t {
	int client_id;
	uint16_t notification_list;
	int signal_type;
	int token;
} __packed;

/*
 * Android 10.0: switch_logging_mode structure
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-10.0.0_r0.87/drivers/char/diag/diagchar.h
 * Android 11.0.0 (RD1A.201105.003.C1)
 * https://android.googlesource.com/kernel/msm.git/+/refs/tags/android-11.0.0_r0.27/drivers/char/diag/diagchar.h
 */
struct diag_logging_mode_param_t_q {
	uint32_t req_mode;
	uint32_t peripheral_mask;
	uint32_t pd_mask;
	uint8_t mode_param;
	uint8_t diag_id;
	uint8_t pd_val;
	uint8_t reserved;
	int peripheral;
	int device_mask;
} __packed;
#define DIAG_MD_LOCAL		0
#define DIAG_MD_LOCAL_LAST	1
#define DIAG_MD_BRIDGE_BASE	DIAG_MD_LOCAL_LAST
#define DIAG_MD_MDM		(DIAG_MD_BRIDGE_BASE)
#define DIAG_MD_MDM2		(DIAG_MD_BRIDGE_BASE + 1)
#define DIAG_MD_BRIDGE_LAST	(DIAG_MD_BRIDGE_BASE + 2)

struct diag_con_all_param_t {
	uint32_t diag_con_all;
	uint32_t num_peripherals;
	uint32_t upd_map_supported;
};
#define DIAG_IOCTL_QUERY_CON_ALL	40

/*
 * Android 9.0: switch_logging_mode structure
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-9.0.0_r0.31/drivers/char/diag/diagchar.h
 */
struct diag_logging_mode_param_t_pie {
	uint32_t req_mode;
	uint32_t peripheral_mask;
	uint32_t pd_mask;
	uint8_t mode_param;
	uint8_t diag_id;
	uint8_t pd_val;
	uint8_t reserved;
	int peripheral;
} __packed;

/*
 * Android 7.0: switch_logging_mode structure
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-7.1.0_r0.3/drivers/char/diag/diagchar.h
 */
struct diag_logging_mode_param_t {
	uint32_t req_mode;
	uint32_t peripheral_mask;
	uint8_t mode_param;
} __packed;
#define DIAG_CON_APSS		(0x0001)	/* Bit mask for APSS */
#define DIAG_CON_MPSS		(0x0002)	/* Bit mask for MPSS */
#define DIAG_CON_LPASS		(0x0004)	/* Bit mask for LPASS */
#define DIAG_CON_WCNSS		(0x0008)	/* Bit mask for WCNSS */
#define DIAG_CON_SENSORS	(0x0010)	/* Bit mask for Sensors */
#define DIAG_CON_NONE		(0x0000)	/* Bit mask for No SS*/
#define DIAG_CON_ALL		(DIAG_CON_APSS | DIAG_CON_MPSS \
				| DIAG_CON_LPASS | DIAG_CON_WCNSS \
				| DIAG_CON_SENSORS)

/*
 * Structures for ioctl
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/drivers/char/diag/diagchar_core.c
 */

struct diag_buffering_mode_t {
	uint8_t peripheral;
	uint8_t mode;
	uint8_t high_wm_val;
	uint8_t low_wm_val;
} __packed;

#define DIAG_PROC_DCI			1
#define DIAG_PROC_MEMORY_DEVICE		2

struct real_time_vote_t {
	uint16_t proc;
	uint8_t real_time_vote;
};

struct real_time_query_t {
	int real_time;
	int proc;
} __packed;

/*
 * DCI structures
 */
struct diag_dci_client_tbl {
	struct task_struct *client;
	uint16_t list; /* bit mask */
	int signal_type;
	unsigned char dci_log_mask[DCI_LOG_MASK_SIZE];
	unsigned char dci_event_mask[DCI_EVENT_MASK_SIZE];
	unsigned char *dci_data;
	int data_len;
	int total_capacity;
	int dropped_logs;
	int dropped_events;
	int received_logs;
	int received_events;
};

/*
 * Default logging mode and buffer
 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/drivers/char/diag/diag_dci.h
 */

static char buf_read[BUFFER_SIZE] = {};	// From Haotian: improve reliability
// int mode = CALLBACK_MODE;	// Logging mode
static int mode = MEMORY_DEVICE_MODE;	// logging mode
static uint16_t remote_dev = 0; // MSM (0) or not
static int client_id;	// DCI client ID (allocated by diag driver)
static int fd; // file descriptor to /dev/diag

// Handle SIGPIPE ERROR
static void
sigpipe_handler (int signo)
{
	if (signo == SIGPIPE) {
		// LOGD("received SIGPIPE. Exit elegantly...\n");

		/*
		 * Deregister the DCI client
		 */

		/*
		int ret;
		ret = ioctl(fd, DIAG_IOCTL_DCI_DEINIT, &client_id);
		if (ret < 0) {
			LOGD("ioctl DIAG_IOCTL_DCI_DEINIT fails, with ret val = %d\n", ret);
			perror("ioctl DIAG_IOCTL_DCI_DEINIT");
		} else {
			printf("ioctl DIAG_IOCTL_DCI_DEINIT: ret=%d\n", ret);
		}
		*/

		close(fd);
	}
}

static double
get_posix_timestamp ()
{
	struct timeval tv;
	(void) gettimeofday(&tv, NULL);
	return (double)(tv.tv_sec) + (double)(tv.tv_usec) / 1.0e6;
}

typedef struct {
	char *p;
	size_t len;
} BinaryBuffer;

// Read the content of config file.
// If failed, an empty buffer is returned.
static BinaryBuffer
read_diag_cfg (const char *filename)
{
	BinaryBuffer ret;

	FILE *fp = fopen(filename, "rb");
	if (fp == NULL) {
		perror("Error");
		goto fail;
	}
	fseek(fp, 0L, SEEK_END);
	size_t file_sz = ftell(fp);
	fseek(fp, 0L, SEEK_SET);

	if (file_sz > 0 && file_sz <= BUFFER_SIZE) {
		ret.p = (char *) malloc(file_sz);
		if (ret.p == NULL) {
			fprintf(stderr, "Error: Failed to malloc.\n");
			goto fail;
		}
		ret.len = file_sz;
		int retcode = fread(ret.p, sizeof(char), ret.len, fp);
		if (retcode != ret.len) {
			perror("Error");
			free(ret.p);
			goto fail;
		}
	} else {
		fprintf(stderr, "Error: File size inappropriate.\n");
		goto fail;
	}

	return ret;

fail:
	ret.p = NULL;
	ret.len = 0;
	return ret;
}

static void
print_hex (const char *buf, int len)
{
	int i = 0;
	for (i = 0; i < len; i++) {
		printf("%02x ", buf[i]);
		if (((i + 1) % 16) == 0)
			printf("\n");
	}
	if ((i % 16) != 0)
		printf("\n");
}

// Write commands to /dev/diag device.
static int
write_commands (int fd, BinaryBuffer *pbuf_write)
{
	size_t i = 0;
	char *p = pbuf_write->p;

	// Set fd to non-blocking mode
	int flags = fcntl(fd, F_GETFL, 0);
	fcntl(fd, F_SETFL, flags | O_NONBLOCK);

	// Buffer to mask command
	char *send_buf = (char *) malloc(pbuf_write->len + 10);
	if (send_buf == NULL) {
		perror("Error");
		return -1;
	}

	// Metadata for each mask command
	size_t offset = remote_dev ? 8 : 4; // offset of the metadata (4 bytes for MSM, 8 bytes for MDM)
	LOGD("write_commands: offset=%lu remote_dev=%u\n", offset, remote_dev);
	*((int *)send_buf) = htole32(USER_SPACE_DATA_TYPE);
	if (remote_dev) {
		/*
		 * MDM device: should let diag driver know it
		 * Reference: diag_get_remote and diagchar_write
		 * in https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/drivers/char/diag/diagchar_core.c
		 */
		*((int *)send_buf+1) =  -MDM;
	}

	while (i < pbuf_write->len) {
		size_t len = 0;
		while (i + len < pbuf_write->len && p[i + len] != 0x7e) len++;
		if (i + len >= pbuf_write->len)
			break;
		len++;
		if (len >= 3) {
			// memcpy(send_buf + 4, p + i, len);
			memcpy(send_buf + offset, p + i, len);
			//LOGD("Writing %d bytes of data\n", len + 4);
			//print_hex(send_buf, len + 4);
			fflush(stdout);
			// int ret = write(fd, (const void *) send_buf, len + 4);
			int ret = write(fd, (const void *) send_buf, len + offset);
			//LOGD("write_commands: ret=%d\n", ret);
			if (ret < 0) {
				LOGE("write_commands error (len=%lu, offset=%lu): %s\n", len, offset, strerror(errno));
				return -1;
			}
			/*
			 * Read responses after writting each command.
			 * NOTE: This step MUST EXIST. Without it, some phones cannot collect logs for two reasons:
			 *  (1) Ensure every config commands succeeds (otherwise read() will be blocked)
			 *  (2) Clean up the buffer, thus avoiding pollution of later real cellular logs
			 */
			// LOGD("Before read\n");
			int read_len = read(fd, buf_read, sizeof(buf_read));
			if (read_len < 0) {
				LOGE("write_commands read error: %s\n", strerror(errno));
				return -1;
			} else {
				// LOGD("Reading %d bytes of resp\n", read_len);
				// LOGD("write_commands responses\n");
				// print_hex(buf_read, read_len);
			}
			// LOGD("After read\n");
		}
		i += len;
	}

	return 0;
}

// Manage the output of logs.
struct LogManagerState {
	const char *dir;
	int log_id;		// ID of the current log.
	FILE *log_fp;		// Point to the current log.
	size_t log_size;	// Number of bytes in the current log.
	size_t log_cut_size;	// Max number of bytes for each log.
};

static void
manager_init_state (struct LogManagerState *pstate, const char *dir, size_t log_cut_size)
{
	pstate->dir = dir;
	pstate->log_id = -1;
	pstate->log_fp = NULL;
	pstate->log_size = -1;
	pstate->log_cut_size = log_cut_size;
}

static void
manager_get_log_name (struct LogManagerState *pstate, char *out_buf, size_t out_buf_size)
{
	assert(out_buf_size > 0);
	size_t dir_len = strlen(pstate->dir);
	// Remove trailing slashes
	while (dir_len > 0 && pstate->dir[dir_len - 1] == '/') {
		dir_len--;
	}
	assert(dir_len > 0);
	assert(out_buf_size > dir_len + 100);
	strncpy(out_buf, pstate->dir, dir_len);
	snprintf(out_buf + dir_len, out_buf_size - dir_len - 1, "/%d.mi2log", pstate->log_id);
	out_buf[out_buf_size - 1] = '\0';
	return;
}

static int
manager_start_new_log (struct LogManagerState *pstate, int fifo_fd)
{
	static char filename[1024] = {};
	int ret;
	if (pstate->log_fp != NULL) {	// end the last log
		assert(pstate->log_id >= 0);
		manager_get_log_name(pstate, filename, sizeof(filename));
		short fifo_msg_type = FIFO_MSG_TYPE_END_LOG_FILE;
		short msg_len = strlen(filename);

		// Wirte msg type to pipe
		ret = write(fifo_fd, &fifo_msg_type, sizeof(short));
		if (ret < 0) {
			return -1;
		}

		// Write len of filename
		ret = write(fifo_fd, &msg_len, sizeof(short));
		if (ret < 0) {
			return -1;
		}

		// Write filename of ended log to pipe
		ret = write(fifo_fd, filename, msg_len);
		if (ret < 0) {
			return -1;
		}

		fclose(pstate->log_fp);
		pstate->log_fp = NULL;
	}
	pstate->log_id = (pstate->log_id < 0? 0: pstate->log_id + 1);
	manager_get_log_name(pstate, filename, sizeof(filename));
	pstate->log_fp = fopen(filename, "wb");
	LOGD("creating %s ...\n", filename);
	if (pstate->log_fp != NULL) {
		// printf("success\n");
		pstate->log_size = 0;
		short fifo_msg_type = FIFO_MSG_TYPE_START_LOG_FILE;
		short msg_len = strlen(filename);
		// Wirte msg type to pipe
		ret = write(fifo_fd, &fifo_msg_type, sizeof(short));
		if (ret < 0) {
			return -1;
		}

		// Write len of filename
		ret = write(fifo_fd, &msg_len, sizeof(short));
		if (ret < 0) {
			return -1;
		}

		// Write filename of ended log to pipe
		ret = write(fifo_fd, filename, msg_len);
		if (ret < 0) {
			return -1;
		}
		// char tmp[4096];
		// sprintf(tmp, "su -c chmod 644 %s\n", filename);
		// system(tmp);
		char tmp[4096];
		sprintf(tmp, "chmod 777 %s\n", filename);
		system(tmp);
	} else {
		return -1;
	}
	return 0;
}

// When appending new data to logs, call this function to maintain states.
// If the size of the current log exceeds log_cut_size, a new log file is created.
static int
manager_append_log (struct LogManagerState *pstate, int fifo_fd, size_t msg_len)
{

	if (pstate->log_size + msg_len > pstate->log_cut_size) {
		int ret = manager_start_new_log(pstate, fifo_fd);
		if (ret < 0) {
			return -1;
		}
	}
	pstate->log_size += msg_len;
	return 0;
}

/*
 * Explicitly probe the length of the argument that ioctl(fd, req, ...) takes.
 *
 * Assumptions:
 *  1. The length is fixed.
 *  2. The insufficient length is the only reason to make ioctl(fd, req, ...)
 *     fail and set errno to EFAULT.
 *  3. The argument filled with 0x3f won't cause unrecoverable errors, or
 *     interfere with what we're going to do next.
 */
static ssize_t
probe_ioctl_arglen (int req, size_t maxlen)
{
	size_t pagesize = sysconf(_SC_PAGESIZE);
	char *p;
	size_t len;

	if (maxlen > pagesize) {
		LOGE("probe_ioctl_arglen: maxlen > pagesize is not implemented\n");
		return -1;
	}

	p = mmap(NULL, pagesize * 2, PROT_READ | PROT_WRITE, MAP_ANONYMOUS | MAP_PRIVATE, 0, 0);
	if (p == MAP_FAILED) {
		LOGE("probe_ioctl_arglen: mmap fails (%s)\n", strerror(errno));
		return -1;
	}
	p += pagesize;
	munmap(p, pagesize);
	memset(p - maxlen, 0x3f, maxlen);

	for (len = 0; len <= maxlen; ++len) {
		if (ioctl(fd, req, p - len) >= 0)
			break;
		if (errno != EFAULT)
			break;
	}
	munmap(p - pagesize, pagesize);
	return len;
}

/*
 * Calling functions into libdiag.so will create several threads. For example,
 * in diag_switch_logging, three threads (disk_write_hdl, qsr4_db_parser_thread_hdl,
 * db_write_thread_hdl) will be created. But actually we don't need them at all.
 * Meanwhile we cannot call dlclose when these useless threads are still alive.
 * So the following fake pthread_create is used to prevent them from being created.
 *
 * Note this fake pthread_create may cause some unexpected side effects on another
 * untested version of libdiag.so. If so, futher modification is needed.
 *
 * Tested devices:
 *   Xiaomi Mi 5S            Android 7.1.2
 *   Huawei Nexus 6P         Android 8.0.0
 *   Xiaomi Redmi Note 8     Android 10.0.0
 *   Samsung Galaxy A90 5G   Android 10.0.0
 */
int
pthread_create (pthread_t *thread, const pthread_attr_t *attr,
                void *(*start_routine)(void *), void *arg) {
	*thread = 1;
	return 0;
}

static int
__enable_logging_libdiag (int mode)
{
	static char libdiag_copycmd[256];
	const char *LIB_DIAG_PATH[] = {
		"/system/vendor/lib64/libdiag.so",
		"/system/vendor/lib/libdiag.so",
	};

	int ret;
	const char *err;
	void *handle;
	void (*diag_switch_logging)(int, const char *);
	int *diag_fd;
	int *logging_mode;

	/*
	 * "Starting in Android 7.0, the system prevents apps from dynamically linking against
	 * non-NDK libraries, which may cause your app to crash."
	 * Reference: https://developer.android.com/about/versions/nougat/android-7.0-changes#ndk
	 *
	 * Copy it into LIBDIAG_TMPPATH and load it.
	 */
	handle = NULL;
	for (unsigned int i = 0; i < sizeof(LIB_DIAG_PATH) / sizeof(LIB_DIAG_PATH[0]) && !handle; ++i) {
		sprintf(libdiag_copycmd, "su -c cp %s " LIBDIAG_TMPPATH "\n", LIB_DIAG_PATH[i]);
		system(libdiag_copycmd);
		handle = dlopen(LIBDIAG_TMPPATH, RTLD_NOW);
		if (!handle)
			LOGE("dlopen %s failed (%s)\n", LIB_DIAG_PATH[i], dlerror());
		else
			LOGI("dlopen %s succeeded\n", LIB_DIAG_PATH[i]);
	}
	if (!handle)
		return -1;

	// Note diag_switch_logging does NOT have a return value in general.
	err = "diag_switch_logging";
	diag_switch_logging = (void (*)(int, const char *)) dlsym(handle, "diag_switch_logging");
	if (!diag_switch_logging)
		goto fail;
	err = "diag_fd/fd";
	diag_fd = (int *) dlsym(handle, "diag_fd");
	if (!diag_fd)
		diag_fd = (int *) dlsym(handle, "fd");
	if (!diag_fd)
		goto fail;
	logging_mode = (int *) dlsym(handle, "logging_mode");

	/*
	 * It seems that calling Diag_LSM_Init here is not necessary.
	 *
	 * When diag_fd is not set, Diag_LSM_Init will try to open
	 * /dev/diag, which will fail since we've already opened one
	 * (errno=EEXIST).
	 *
	 * When diag_fd is set, Diag_LSM_Init will also do nothing
	 * related to our goal.
	 */
	*diag_fd = fd;
	(*diag_switch_logging)(mode, NULL);

	if (logging_mode && *logging_mode != mode) {
		LOGE("diag_switch_logging in libdiag.so failed\n");
		ret = -1;
	} else if (!logging_mode) {
		LOGW("Missing symbol logging_mode in libdiag.so, "
		     "assume diag_switch_logging succeeded\n");
		ret = 0;
	} else {
		ret = 0;
	}

	// We have never created new threads in libdiag.so, so we can close it.
	dlclose(handle);
	return ret;
fail:
	LOGE("Missing symbol %s in libdiag.so\n", err);
	dlclose(handle);
	return -1;
}

static int
enable_logging (int fd, int mode)
{
	int ret = -1;

	/*
	 * EXPERIMENTAL (NEXUS 6 ONLY):
	 * 1. check remote_dev
	 * 2. Register a DCI client
	 * 3. Send DCI control command
	 */
	ret = ioctl(fd, DIAG_IOCTL_REMOTE_DEV, &remote_dev);
	if (ret < 0) {
		printf("ioctl DIAG_IOCTL_REMOTE_DEV fails, with ret val = %d\n", ret);
		perror("ioctl DIAG_IOCTL_REMOTE_DEV");
	} else {
		LOGD("DIAG_IOCTL_REMOTE_DEV remote_dev=%d\n", remote_dev);
	}

	// Register a DCI client
	struct diag_dci_reg_tbl_t dci_client;
	dci_client.client_id = 0;
	dci_client.notification_list = 0;
	dci_client.signal_type = SIGPIPE;
	// dci_client.token = remote_dev;
	dci_client.token = 0;
	ret = ioctl(fd, DIAG_IOCTL_DCI_REG, &dci_client);
	if (ret < 0) {
		printf("ioctl DIAG_IOCTL_DCI_REG fails, with ret val = %d\n", ret);
		perror("ioctl DIAG_IOCTL_DCI_REG");
	} else {
		client_id = ret;
		printf("DIAG_IOCTL_DCI_REG client_id=%d\n", client_id);
	}

	// Nexus-6-only logging optimizations
	// It will fail on other devices (errno=EFAULT), since DIAG_IOCTL_OPTIMIZED_LOGGING is equal to DIAG_IOCTL_PERIPHERAL_BUF_CONFIG.
	// Reference: https://github.com/MotorolaMobilityLLC/kernel-msm/blob/kitkat-4.4.4-release-victara/drivers/char/diag/diagchar_core.c#L1189
	// ret = ioctl(fd, DIAG_IOCTL_OPTIMIZED_LOGGING, (long) 1);
	// if (ret >= 0) {
	// 	ret = ioctl(fd, DIAG_IOCTL_OPTIMIZED_LOGGING_FLUSH, NULL);
	// 	if (ret < 0) {
	// 		printf("ioctl DIAG_IOCTL_OPTIMIZED_LOGGING_FLUSH fails, with ret val = %d\n", ret);
	// 		perror("ioctl DIAG_IOCTL_OPTIMIZED_LOGGING_FLUSH");
	// 	}
	// }

	/*
	 * TODO: cleanup the diag before start
	 * 1. Drain the buffer: prevent outdate logs next time
	 * 2. Clean up masks: prevent enable_log bug next time
	 */

	/*
	 * DIAG_IOCTL_LSM_DEINIT, try if it can clear buffer
	 */

	/*
	ret = ioctl(fd, DIAG_IOCTL_LSM_DEINIT, NULL);
	if (ret < 0) {
		printf("ioctl DIAG_IOCTL_LSM_DEINIT fails, with ret val = %d\n", ret);
		perror("ioctl DIAG_IOCTL_LSM_DEINIT");
	}
	*/

	// ret = ioctl(fd, DIAG_IOCTL_DCI_CLEAR_LOGS, &client_id);
	// if (ret < 0) {
	// 	printf("ioctl DIAG_IOCTL_DCI_CLEAR_LOGS fails, with ret val = %d\n", ret);
	// 	perror("ioctl DIAG_IOCTL_DCI_CLEAR_LOGS");
	// }
	// ret = ioctl(fd, DIAG_IOCTL_DCI_CLEAR_EVENTS, &client_id);
	// if (ret < 0) {
	// 	printf("ioctl DIAG_IOCTL_DCI_CLEAR_EVENTS fails, with ret val = %d\n", ret);
	// 	perror("ioctl DIAG_IOCTL_DCI_CLEAR_EVENTS");
	// }

	/*
	 * EXPERIMENTAL (NEXUS 6 ONLY): configure the buffering mode to circular
	 */
	struct diag_buffering_mode_t buffering_mode;
	// buffering_mode.peripheral = remote_dev;
	buffering_mode.peripheral = 0;
	buffering_mode.mode = DIAG_BUFFERING_MODE_STREAMING;
	buffering_mode.high_wm_val = DEFAULT_HIGH_WM_VAL;
	buffering_mode.low_wm_val = DEFAULT_LOW_WM_VAL;

	ret = ioctl(fd, DIAG_IOCTL_PERIPHERAL_BUF_CONFIG, &buffering_mode);
	if (ret < 0) {
		printf("ioctl DIAG_IOCTL_PERIPHERAL_BUF_CONFIG fails, with ret val = %d\n", ret);
		//perror("ioctl DIAG_IOCTL_PERIPHERAL_BUF_CONFIG");
	}

	// uint8_t peripheral = 0;
	// for (; peripheral <= LAST_PERIPHERAL; peripheral++) {
	// 	ret = ioctl(fd, DIAG_IOCTL_PERIPHERAL_BUF_DRAIN, &peripheral);
	// 	if (ret < 0) {
	// 		printf("ioctl DIAG_IOCTL_PERIPHERAL_BUF_DRAIN fails, with ret val = %d\n", ret);
	// 		perror("ioctl DIAG_IOCTL_PERIPHERAL_BUF_DRAIN");
	// 	}

	// 	/*
	// 	 * EXPERIMENTAL (NEXUS 6 ONLY): configure the buffering mode to circular
	// 	*/
	// 	struct diag_buffering_mode_t buffering_mode;
	// 	buffering_mode.peripheral = peripheral;
	// 	buffering_mode.mode = DIAG_BUFFERING_MODE_STREAMING;
	// 	buffering_mode.high_wm_val = DEFAULT_HIGH_WM_VAL;
	// 	buffering_mode.low_wm_val = DEFAULT_LOW_WM_VAL;
	//
	// 	ret = ioctl(fd, DIAG_IOCTL_PERIPHERAL_BUF_CONFIG, &buffering_mode);
	// 	if (ret < 0) {
	// 		printf("ioctl DIAG_IOCTL_PERIPHERAL_BUF_CONFIG fails, with ret val = %d\n", ret);
	// 		perror("ioctl DIAG_IOCTL_PERIPHERAL_BUF_CONFIG");
	// 	}
	// }

	/*
	 * Enable logging mode:
	 *
	 * DIAG_IOCTL_SWITCH_LOGGING has multiple versions. They require different arguments (which have
	 * different fields and whose lengths are also different). However, it seems there is no way to
	 * directly determine the version of DIAG_IOCTL_SWITCH_LOGGING. So some tricks can not be avoided
	 * here.
	 *
	 * A traditional way is to try one by one. But it can cause undefined behaviour. Specially, when
	 * a new verison of DIAG_IOCTL_SWITCH_LOGGING is introduced, it may not report an error. But some
	 * new fields will be out of bounds. Consequently, it may cause random bugs, which is confusing.
	 *
	 * So a more elegant way is to explicitly probe the length of DIAG_IOCTL_SWITCH_LOGGING's argument.
	 * And the version can be deduced from the length. It is not very precise, but it is enough at least
	 * for now.
	 */
	// Testing: get device info
	char *board_pf_cmd = "su -c getprop ro.board.platform";
	char board_name[256];
    FILE *fp;
    if ((fp = popen(board_pf_cmd, "r")) != NULL) {
        while (fgets(board_name, 256, fp) != NULL) {
        	// printf("OUTPUT: %s\n", board_name);
    	}
    	pclose(fp);
    }

	char *sys_ver_cmd = "su -c getprop ro.build.version.release";
    char system_version[256];
    if ((fp = popen(sys_ver_cmd, "r")) != NULL) {
        while (fgets(system_version, 256, fp) != NULL) {
        	// printf("OUTPUT: %s\n", system_version);
    	}
    	pclose(fp);
    }

    ssize_t arglen = probe_ioctl_arglen(DIAG_IOCTL_SWITCH_LOGGING, sizeof(struct diag_logging_mode_param_t_q));
    
    if (strstr(board_name, "lito") != NULL && strstr(system_version, "11") != NULL){
    	printf("MATCHED.\n");
    	/* Android 11.0.0 (RD1A.201105.003.C1)
		 * Reference:
		 *   https://android.googlesource.com/kernel/msm.git/+/refs/tags/android-11.0.0_r0.27/drivers/char/diag/diagchar_core.c
		 */
		struct diag_logging_mode_param_t_q new_mode;
		struct diag_con_all_param_t con_all;
        	con_all.diag_con_all = 0xff;
		ret = ioctl(fd, DIAG_IOCTL_QUERY_CON_ALL, &con_all);
		if (ret == 0)
			new_mode.peripheral_mask = con_all.diag_con_all;
		else
			new_mode.peripheral_mask = 0x7f;
		new_mode.req_mode = mode;
		new_mode.pd_mask = 0;
		new_mode.mode_param = 1;
		new_mode.diag_id = 0;
		new_mode.pd_val = 0;
		new_mode.peripheral = 0;
		new_mode.device_mask = 1 << DIAG_MD_LOCAL;
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, &new_mode);
		printf("Enable for Android 11: %d\n", ret);
		goto next;
    }
	// Testing end

	// LOGD("arglen=%ld, target=%lu\n", arglen, sizeof(struct diag_logging_mode_param_t_r));
	switch (arglen) {
	
	case (sizeof(struct diag_logging_mode_param_t_q)): {
		/* Android 10.0 mode
		 * Reference:
		 *   https://android.googlesource.com/kernel/msm.git/+/android-10.0.0_r0.87/drivers/char/diag/diagchar_core.c
		 *   and the disassembly code of libdiag.so
		 */
		struct diag_logging_mode_param_t_q new_mode;
		struct diag_con_all_param_t con_all;
        	con_all.diag_con_all = 0xff;
		ret = ioctl(fd, DIAG_IOCTL_QUERY_CON_ALL, &con_all);
		if (ret == 0)
			new_mode.peripheral_mask = con_all.diag_con_all;
		else
			new_mode.peripheral_mask = 0x7f;
		new_mode.req_mode = mode;
		new_mode.peripheral_mask = DIAG_CON_ALL;
		new_mode.pd_mask = 0;
		new_mode.mode_param = 1;
		new_mode.diag_id = 0;
		new_mode.pd_val = 0;
		new_mode.peripheral = -22;
		new_mode.device_mask = 1 << DIAG_MD_LOCAL;
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, &new_mode);
	
	    if(ret >= 0)	
		    break;
	}
	case sizeof(struct diag_logging_mode_param_t_pie): {
		/* Android 9.0 mode
		 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-9.0.0_r0.31/drivers/char/diag/diagchar_core.c
		 */
		struct diag_logging_mode_param_t_pie new_mode;
		new_mode.req_mode = mode;
		new_mode.mode_param = 0;
		new_mode.pd_mask = 0;
		new_mode.peripheral_mask = DIAG_CON_ALL;
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, &new_mode);
		
		if(ret >= 0)
		    break;
	}
	case sizeof(struct diag_logging_mode_param_t): {
		/* Android 7.0 mode
		 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-7.1.0_r0.3/drivers/char/diag/diagchar_core.c
		 */
		struct diag_logging_mode_param_t new_mode;
		new_mode.req_mode = mode;
		new_mode.peripheral_mask = DIAG_CON_ALL;
		new_mode.mode_param = 0;
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, &new_mode);
		
		if(ret >= 0)
		  break;
	}
	case sizeof(int):
		/* Android 6.0 mode
		 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-6.0.0_r0.9/drivers/char/diag/diagchar_core.c
		 */
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, &mode);
		if (ret >= 0)
		    break;
		/*
		 * Is it really necessary? It seems that the kernel will simply ignore all the fourth and subsequent
		 * arguments of ioctl. But similar lines do exist in libdiag.so. Why?
		 * Reference: https://android.googlesource.com/kernel/msm.git/+/android-10.0.0_r0.87/fs/ioctl.c#692
		 */
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, &mode, 12, 0, 0, 0, 0);
		if (ret >= 0)
		    break;
	case 0:
		// Yuanjie: the following works for Samsung S5
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, (long) mode);
		if (ret >= 0)
		    break;
		// Same question as above: Is it really necessary?
		// Yuanjie: the following is used for Xiaomi RedMi 4
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, (long) mode, 12, 0, 0, 0, 0);
		if (ret >= 0)
		    break;
	default:
		LOGW("ioctl DIAG_IOCTL_SWITCH_LOGGING with arglen=%ld is not supported\n", arglen);
		ret = -8080;
		break;
	}
next:
	// printf("Reach the next\n");
	if (ret < 0 && ret != -8080)
		LOGE("ioctl DIAG_IOCTL_SWITCH_LOGGING with arglen=%ld is supported, "
		     "but it failed (%s)\n", arglen, strerror(errno));
	else if (ret >= 0)
		LOGI("ioctl DIAG_IOCTL_SWITCH_LOGGING with arglen=%ld succeeded\n", arglen);
		// printf("ioctl DIAG_IOCTL_SWITCH_LOGGING with arglen=%ld succeeded\n", arglen);

	if (ret < 0) {
		/* Ultimate approach: Use libdiag.so */
		ret = __enable_logging_libdiag(mode);
		if (ret >= 0)
			LOGI("Using libdiag.so to switch logging succeeded\n");
	}
	if (ret >= 0) {
		// LOGD("Enable logging mode success.\n");

		// Register a DCI client
		struct diag_dci_reg_tbl_t dci_client;
		dci_client.client_id = 0;
		dci_client.notification_list = 0;
		dci_client.signal_type = SIGPIPE;
		// dci_client.token = remote_dev;
		dci_client.token = 0;
		ret = ioctl(fd, DIAG_IOCTL_DCI_REG, &dci_client);
		if (ret < 0) {
			// LOGD("ioctl DIAG_IOCTL_DCI_REG fails, with ret val = %d\n", ret);
			// perror("ioctl DIAG_IOCTL_DCI_REG");
		} else {
			client_id = ret;
			// LOGD("DIAG_IOCTL_DCI_REG client_id=%d\n", client_id);
		}

		/*
		 * Configure the buffering mode to circular
		 */
		struct diag_buffering_mode_t buffering_mode;
		// buffering_mode.peripheral = remote_dev;
		buffering_mode.peripheral = 0;
		buffering_mode.mode = DIAG_BUFFERING_MODE_STREAMING;
		buffering_mode.high_wm_val = DEFAULT_HIGH_WM_VAL;
		buffering_mode.low_wm_val = DEFAULT_LOW_WM_VAL;

		ret = ioctl(fd, DIAG_IOCTL_PERIPHERAL_BUF_CONFIG, &buffering_mode);
		if (ret < 0) {
			// LOGD("ioctl DIAG_IOCTL_PERIPHERAL_BUF_CONFIG fails, with ret val = %d\n", ret);
			// perror("ioctl DIAG_IOCTL_PERIPHERAL_BUF_CONFIG");
		}

	} else {
		// LOGD("Failed to enable logging mode: %s.\n", strerror(errno));
	}

	return ret;
}

int
main (int argc, char **argv)
{
	if (signal(SIGPIPE, sigpipe_handler) == SIG_ERR) {
		LOGW("WARNING: diag_revealer cannot capture SIGPIPE\n");
	}

	if (argc < 3 || argc > 5) {
		printf("Diag_revealer " DIAG_REVEALER_VERSION "\n");
		printf("Author: Yuanjie Li, Jiayao Li, Ruihan Li\n");
		printf("UCLA Wing Group, PKU SOAR Group\n");
		printf("Usage: diag_revealer DIAG_CFG_PATH FIFO_PATH [LOG_OUTPUT_DIR] [LOG_CUT_SIZE (in MB)]\n");
		return 0;
	}

	// Read config file
	BinaryBuffer buf_write = read_diag_cfg(argv[1]);
	if (buf_write.p == NULL || buf_write.len == 0) {
		return -8001;
	}
	// print_hex(buf_write.p, buf_write.len);

	// system("su -c chmod 777 /dev/diag");

	// int fd = open("/dev/diag", O_RDWR);
	// fd = open("/dev/diag", O_RDWR);
	fd = open("/dev/diag", O_RDWR | O_LARGEFILE | O_NONBLOCK);
	if (fd < 0) {
		perror("open diag dev");
		return -8002;
	}

	int ret;

	/*
	 * Enable logging mode
	 */
	enable_logging(fd, mode);

	// Write commands to /dev/diag device to enable log collecting.
	// LOGD("Before write_commands\n");
	ret = write_commands(fd, &buf_write);
	fflush(stdout);
	free(buf_write.p);
	if (ret != 0) {
		return -8004;
	}

	// Messages are output to this FIFO pipe
	int pipesize = DIAG_FIFO_PIPE_SIZE;

	// Set max frame pipe size: Prevent packet loss
	char tmp[4096];
	sprintf(tmp, "su -c \"echo -e %d > /proc/sys/fs/pipe-max-size\"", pipesize);
	system(tmp);
	// system("su -c \"ulimit -l unlimited\"");

	struct rlimit rl;
	rl.rlim_max = pipesize;
	rl.rlim_cur = pipesize;
	setrlimit (RLIMIT_MEMLOCK, &rl);
	getrlimit (RLIMIT_CPU, &rl);

	// int fifo_fd = open(argv[2], O_WRONLY | O_NONBLOCK);	// block until the other end also calls open()
	int fifo_fd = open(argv[2], O_WRONLY);	// block until the other end also calls open()
	if (fifo_fd < 0) {
		perror("open fifo");
		return -8005;
	} else {
		// LOGD("FIFO opened\n");
	}

	int res = fcntl(fifo_fd, F_SETPIPE_SZ, pipesize);
	if (res < 0)
		LOGI("Failed to set FIFO: %s\n", strerror(errno));

	res = fcntl(fifo_fd, F_GETPIPE_SZ, pipesize);
	LOGI("FIFO capacity: %d\n", res);

	struct LogManagerState state;
	// Initialize state
	manager_init_state(&state, NULL, 0);

	if (argc >= 4) {
		size_t log_cut_size = 0;
		if (argc == 5) {
			double size_MB = atof(argv[4]);
			if (size_MB <= 0.0) {
				size_MB = 1.0;
				fprintf(stderr, "log_cut_size inappropriate, reset to %.2f\n", size_MB);
			}
			log_cut_size = (size_t) (size_MB * 1024 * 1024);
		} else {
			log_cut_size = LOG_CUT_SIZE_DEFAULT;
		}
		manager_init_state(&state, argv[3], log_cut_size);

		printf("log_cut_size = %lld\n", (long long int) log_cut_size);

		int ret2 = manager_start_new_log(&state, fifo_fd);
		if (ret2 < 0 || state.log_fp == NULL) {
			perror("open diag log");
			return -8006;
		}
	}

	while (1) {
		// LOGI("Reading logs...\n");
		int read_len = read(fd, buf_read, sizeof(buf_read));
		// LOGI("Received logs. read_len=%d\n", read_len);
		if (read_len > 0) {
			if (*((int *)buf_read) == USER_SPACE_DATA_TYPE) {
				int num_data = *((int *)(buf_read + 4));
				// LOGI("num_data=%d\n", num_data);
				int i = 0;
				// long long offset = 8;
				long long offset = remote_dev ? 12 : 8;
				for (i = 0; i < num_data; i++) {
					int ret_err;
					short fifo_msg_type = FIFO_MSG_TYPE_LOG;
					short fifo_msg_len;
					double ts = get_posix_timestamp();

					// Copy msg_len
					int msg_len = 0;
					memcpy(&msg_len, buf_read + offset, sizeof(int));
					// memcpy(&msg_len, buf_read + offset + 4, sizeof(int));
					// LOGI("memcpy: msg_len=%d\n", msg_len);
					if (msg_len < 0)
						continue;
					// print_hex(buf_read + offset + 4, msg_len);
					// Wirte msg type to pipe

					// LOGD("ret_err0");
					ret_err = write(fifo_fd, &fifo_msg_type, sizeof(short));

					// Write size of (payload + timestamp)
					fifo_msg_len = (short) msg_len + 8;
					ret_err = write(fifo_fd, &fifo_msg_len, sizeof(short));
					if (ret_err < 0) {
						// LOGI("Pipe closed, diag_revealer will exit");
						LOGI("Pipe error (msg_len): %s", strerror(errno));
						close(fd);
						return -1;
					}

					// Write timestamp of sending payload to pipe
					ret_err = write(fifo_fd, &ts, sizeof(double));
					if (ret_err < 0) {
						// LOGI("Pipe closed, diag_revealer will exit");
						LOGI("Pipe error (timestamp): %s", strerror(errno));
						close(fd);
						return -1;
					}

					// Write payload to pipe
					ret_err = write(fifo_fd, buf_read + offset + 4, msg_len);
					if (ret_err < 0) {
						LOGI("Pipe error (payload): %s", strerror(errno));
						LOGD("Debug: msg_len=%d buf_read+offset+4=%s\n", msg_len, buf_read + offset + 4);
						// LOGI("Pipe closed, diag_revealer will exit");
						close(fd);
						return -1;
					}

					// Write mi2log output if necessary
					if (state.log_fp != NULL) {
						int ret2 = manager_append_log(&state, fifo_fd, msg_len);
						if (ret2 == 0) {
							size_t log_res = fwrite(buf_read + offset + 4, sizeof(char), msg_len, state.log_fp);
							if (log_res != msg_len) {
								LOGI("Fail to save logs. diag_revealer will exit");
								close(fd);
								return -1;
							}
							fflush(state.log_fp);
						} else {
							// TODO: error handling
							LOGI("Fail to append logs. diag_revealer will exit");
							close(fd);
							return -1;
						}
					}
					offset += msg_len + 4;
				}
			} else {
				// TODO: Check other raw binary types
				// LOGI("Not USER_SPACE_DATA_TYPE: %d\n", *((int *)buf_read));
			}
		} else {
			continue;
		}
	}

	/*
	 * Deregister the DCI client
	 */

	/*
	ret = ioctl(fd, DIAG_IOCTL_DCI_DEINIT, &client_id);
	if (ret < 0) {
		LOGD("ioctl DIAG_IOCTL_DCI_DEINIT fails, with ret val = %d\n", ret);
		perror("ioctl DIAG_IOCTL_DCI_DEINIT");
	} else {
		printf("ioctl DIAG_IOCTL_DCI_DEINIT: ret=%d\n", ret);
	}
	*/

	close(fd);

	return (ret < 0 ? ret : 0);
}
