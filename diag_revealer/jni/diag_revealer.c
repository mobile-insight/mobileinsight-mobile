/* diag_revealer.c
 * Author: Jiayao Li
 * Read diagnostic message from Android's /dev/diag device. Messages are output
 * using a Linux FIFO pipe.
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
#include <sys/ioctl.h>
#include <sys/time.h>
// #include <linux/diagchar.h>
#define _GNU_SOURCE 
#define F_SETPIPE_SZ (F_LINUX_SPECIFIC_BASE + 7) 
#define F_GETPIPE_SZ (F_LINUX_SPECIFIC_BASE + 8)
#include <fcntl.h>

#include <android/log.h>
#define  LOG_TAG    "diag_revealer"

#define  LOGE(...)  __android_log_print(ANDROID_LOG_ERROR,LOG_TAG,__VA_ARGS__)
#define  LOGW(...)  __android_log_print(ANDROID_LOG_WARN,LOG_TAG,__VA_ARGS__)
#define  LOGD(...)  __android_log_print(ANDROID_LOG_DEBUG,LOG_TAG,__VA_ARGS__)
#define  LOGI(...)  __android_log_print(ANDROID_LOG_INFO,LOG_TAG,__VA_ARGS__)

// NOTE: the following number should be updated every time.
#define DIAG_REVEALER_VERSION "1.2.0"

#define LOG_CUT_SIZE_DEFAULT (1 * 1024 * 1024)
// #define BUFFER_SIZE	8192
#define BUFFER_SIZE	32768

#define FIFO_MSG_TYPE_LOG 1
#define FIFO_MSG_TYPE_START_LOG_FILE 2
#define FIFO_MSG_TYPE_END_LOG_FILE 3

#define USER_SPACE_DATA_TYPE	0x00000020
#define CALLBACK_DATA_TYPE		0x00000080
#define DIAG_IOCTL_SWITCH_LOGGING	7
#define DIAG_IOCTL_REMOTE_DEV		32
#define DIAG_IOCTL_DCI_CLEAR_LOGS	28
#define DIAG_IOCTL_DCI_CLEAR_EVENTS	29

#define MEMORY_DEVICE_MODE		2
#define CALLBACK_MODE		6

#define DIAG_IOCTL_REMOTE_DEV		32
#define DIAG_IOCTL_VOTE_REAL_TIME	33
#define DIAG_IOCTL_GET_REAL_TIME	34
#define DIAG_IOCTL_PERIPHERAL_BUF_CONFIG	35
#define DIAG_IOCTL_PERIPHERAL_BUF_DRAIN		36

#define DIAG_BUFFERING_MODE_STREAMING	0
#define DEFAULT_LOW_WM_VAL	15
#define DEFAULT_HIGH_WM_VAL	85
#define NUM_SMD_DATA_CHANNELS 4
#define NUM_SMD_CONTROL_CHANNELS NUM_SMD_DATA_CHANNELS

#define MODEM_DATA		0
#define LAST_PERIPHERAL 3

typedef struct {
	char *p;
	size_t len;
} BinaryBuffer;

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

char buf_read[BUFFER_SIZE] = {};	// From Haotian: improve reliability
// int mode = CALLBACK_MODE;	// Logging mode
int mode = MEMORY_DEVICE_MODE;


// Handle SIGPIPE ERROR
void sigpipe_handler(int signo)
{
  if (signo == SIGPIPE){
  	  // LOGD("received SIGPIPE. Exit elegantly...\n");
  }
}


static double
get_posix_timestamp () {
    struct timeval tv;
    (void) gettimeofday(&tv, NULL);
    return (double)(tv.tv_sec) + (double)(tv.tv_usec) / 1.0e6;
}

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
	char *send_buf = (char *) malloc(pbuf_write->len + 10);
	if (send_buf == NULL) {
		perror("Error");
		return -1;
	}
	*((int *)send_buf) = htole32(USER_SPACE_DATA_TYPE);

	while (i < pbuf_write->len) {
		size_t len = 0;
		while (i + len < pbuf_write->len && p[i + len] != 0x7e) len++;
		if (i + len >= pbuf_write->len)
			break;
		len++;
		if (len >= 3) {
			memcpy(send_buf + 4, p + i, len);
			// LOGD("Writing %d bytes of data\n", len + 4);
			// print_hex(send_buf, len + 4);
			fflush(stdout);
			int ret = write(fd, (const void *) send_buf, len + 4);
			// LOGD("write_commands: ret=%d\n",ret);
			if (ret < 0) {
				perror("cmd write error");
				return -1;
			}
			int read_len = read(fd, buf_read, sizeof(buf_read));
			if (read_len < 0) {
				perror("cmd read error");
				return -1;
			} else {
				// LOGD("Reading %d bytes of resp\n", read_len);
			}
		}
		i += len;
	}

	return 0;
}

// Manage the output of logs.
struct LogManagerState {
	const char *dir;
	int log_id;		// ID of the current log.
	FILE *log_fp;	// Point to the current log.
	size_t log_size;	// Number of bytes in the current log.
	size_t log_cut_size;	// Max number of bytes for each log.
};

static void
manager_init_state (struct LogManagerState *pstate, const char *dir, size_t log_cut_size) {
	pstate->dir = dir;
	pstate->log_id = -1;
	pstate->log_fp = NULL;
	pstate->log_size = -1;
	pstate->log_cut_size = log_cut_size;
}

static void
manager_get_log_name (struct LogManagerState *pstate, char *out_buf, size_t out_buf_size) {
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
manager_start_new_log (struct LogManagerState *pstate, int fifo_fd) {
	static char filename[1024] = {};
	int ret;
	if (pstate->log_fp != NULL) {	// end the last log
		assert(pstate->log_id >= 0);
		manager_get_log_name(pstate, filename, sizeof(filename));
		short fifo_msg_type = FIFO_MSG_TYPE_END_LOG_FILE;
		short msg_len = strlen(filename);

		// Wirte msg type to pipe
		ret = write(fifo_fd, &fifo_msg_type, sizeof(short));
		if(ret<0){
			return -1;
		}

		// Write len of filename
		ret = write(fifo_fd, &msg_len, sizeof(short));
		if(ret<0){
			return -1;
		}

		// Write filename of ended log to pipe
		ret = write(fifo_fd, filename, msg_len);
		if(ret<0){
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
		if(ret<0){
			return -1;
		}

		// Write len of filename
		ret = write(fifo_fd, &msg_len, sizeof(short));
		if(ret<0){
			return -1;
		}

		// Write filename of ended log to pipe
		ret = write(fifo_fd, filename, msg_len);
		if(ret<0){
			return -1;
		}
        // char tmp[4096];
        // sprintf(tmp,"su -c chmod 644 %s\n",filename);
        // system(tmp);

	} else {
		return -1;
	}
	return 0;
}

// When appending new data to logs, call this function to maintain states.
// If the size of the current log exceeds log_cut_size, a new log file is created.
static int
manager_append_log (struct LogManagerState *pstate, int fifo_fd, size_t msg_len) {

	if (pstate->log_size + msg_len > pstate->log_cut_size) {
		int ret = manager_start_new_log(pstate, fifo_fd);
		if (ret < 0) {
			return -1;
		}
	}
	pstate->log_size += msg_len;
	return 0;
}

int
main (int argc, char **argv)
{

	if (signal(SIGPIPE, sigpipe_handler) == SIG_ERR) {
		LOGW("WARNING: diag_revealer cannot capture SIGPIPE\n");
	}

	if (argc < 3 || argc > 5) {
		printf("Diag_revealer " DIAG_REVEALER_VERSION "\n");
		printf("Author: Yuanjie Li, Jiayao Li\n");
		printf("UCLA Wing Group\n");
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

	int fd = open("/dev/diag", O_RDWR);
	if (fd < 0) {
		perror("open diag dev");
		return -8002;
	}

	int ret;

	/*
     * TODO: cleanup the diag before exit
     * 1. Drain the buffer: prevent outdate logs next time
     * 2. Clean up masks: prevent enable_log bug next time
     */
    int client_id = 0;
    ret = ioctl(fd, DIAG_IOCTL_DCI_CLEAR_LOGS, (char *) &client_id);  
    if (ret < 0){
        printf("ioctl DIAG_IOCTL_DCI_CLEAR_LOGS fails, with ret val = %d\n", ret);
    	perror("ioctl DIAG_IOCTL_DCI_CLEAR_LOGS");
    }
    ret = ioctl(fd, DIAG_IOCTL_DCI_CLEAR_EVENTS, (char *) &client_id);  
    if (ret < 0){
        printf("ioctl DIAG_IOCTL_DCI_CLEAR_EVENTS fails, with ret val = %d\n", ret);
    	perror("ioctl DIAG_IOCTL_DCI_CLEAR_EVENTS");
    }
    uint8_t peripheral = 0;
    for(;peripheral<=LAST_PERIPHERAL; peripheral++)
    {
    	ret = ioctl(fd, DIAG_IOCTL_PERIPHERAL_BUF_DRAIN, (char *) &peripheral);  
	    if (ret < 0){
	        printf("ioctl DIAG_IOCTL_PERIPHERAL_BUF_DRAIN fails, with ret val = %d\n", ret);
	    	perror("ioctl DIAG_IOCTL_PERIPHERAL_BUF_DRAIN");
	    }
    }

	// Enable logging mode
	/*
	 * Yuanjie: DON'T USE MEMORY_DEVICE_MODE
	 */
	ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, (char *) &mode);  
	if (ret < 0) {
		LOGD("ioctl SWITCH_LOGGING fails, with ret val = %d\n", ret);
		perror("ioctl SWITCH_LOGGING");
		ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, (char *) mode);
		if (ret < 0) {
			LOGD("Alternative ioctl SWITCH_LOGGING fails, with ret val = %d\n", ret);
			perror("Alternative ioctl SWITCH_LOGGING");
		}

	}
	else{
		// printf("Older way of ioctl succeeds.\n");
	}


	// Write commands to /dev/diag device to enable log collecting.
	// LOGD("Before write_commands\n");
	ret = write_commands(fd, &buf_write);
	fflush(stdout);
	free(buf_write.p);
	if (ret != 0) {
		return -8004;
	}

	// Messages are output to this FIFO pipe
	// int fifo_fd = open(argv[2], O_WRONLY | O_NONBLOCK);	// block until the other end also calls open()
	int fifo_fd = open(argv[2], O_WRONLY);	// block until the other end also calls open()
	if (fifo_fd < 0) {
		perror("open fifo");
		return -8005;
	} else {
		// LOGD("FIFO opened\n");
	}
	int pipesize = 1024*1024*128;	//128MB
	fcntl(fifo_fd, F_SETPIPE_SZ, pipesize);

	int res = fcntl(fifo_fd, F_GETPIPE_SZ,pipesize);
	// LOGI("F_GETPIPE_SZ: res=%d pipesize=%d\n",res,pipesize);

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
				// LOGI("num_data=%d\n",num_data);
				int i = 0;
				long long offset = 8;
				for (i = 0; i < num_data; i++) {
					short fifo_msg_type = FIFO_MSG_TYPE_LOG;
					int msg_len;
					short fifo_msg_len;
					double ts = get_posix_timestamp();
					memcpy(&msg_len, buf_read + offset, 4);
					// printf("%d %.5f\n", msg_len, ts);
					// print_hex(buf_read + offset + 4, msg_len);
					// Wirte msg type to pipe
					int ret_err;
					// LOGD("ret_err0");
					ret_err = write(fifo_fd, &fifo_msg_type, sizeof(short));

					// Write size of (payload + timestamp)
					fifo_msg_len = (short) msg_len + 8;
					ret_err = write(fifo_fd, &fifo_msg_len, sizeof(short));
					if(ret_err<0){
						LOGI("Pipe closed, diag_revealer will exit");
						close(fd);
						return -1;
					}

					// Write timestamp of sending payload to pipe
					ret_err = write(fifo_fd, &ts, sizeof(double));
					if(ret_err<0){
						LOGI("Pipe closed, diag_revealer will exit");
						close(fd);
						return -1;
					}

					// Write payload to pipe
					ret_err = write(fifo_fd, buf_read + offset + 4, msg_len);
					if(ret_err<0){
						LOGI("Pipe closed, diag_revealer will exit");
						close(fd);
						return -1;
					}

					// Write mi2log output if necessary
					if (state.log_fp != NULL) {
						int ret2 = manager_append_log(&state, fifo_fd, msg_len);
						if (ret2 == 0) {
							size_t log_res = fwrite(buf_read + offset + 4, sizeof(char), msg_len, state.log_fp);
							if(log_res!=msg_len){
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
			}
			else
			{
				// LOGI("Not USER_SPACE_DATA_TYPE: %d\n", *((int *)buf_read));
			}
		} else {
			continue;
		}
	}

	close(fd);


	return (ret < 0? ret: 0);
}
