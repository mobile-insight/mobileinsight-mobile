#include <endian.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/time.h>
// #include <linux/diagchar.h>

#define DIAG_REVEALER_VERSION "1.0.1"


#define USER_SPACE_DATA_TYPE	0x00000020
#define CALLBACK_DATA_TYPE		0x00000080
#define DIAG_IOCTL_SWITCH_LOGGING	7
#define DIAG_IOCTL_REMOTE_DEV		32
#define MEMORY_DEVICE_MODE	2
#define CALLBACK_MODE		6

#define DIAG_IOCTL_VOTE_REAL_TIME	33
#define DIAG_IOCTL_GET_REAL_TIME	34
#define DIAG_IOCTL_PERIPHERAL_BUF_CONFIG	35
#define DIAG_IOCTL_PERIPHERAL_BUF_DRAIN		36

#define DIAG_BUFFERING_MODE_STREAMING	0
#define DEFAULT_LOW_WM_VAL	15
#define DEFAULT_HIGH_WM_VAL	85
#define NUM_SMD_CONTROL_CHANNELS 4

#define MODEM_DATA		0

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

char buf_read[4096] = {};

static double
get_posix_timestamp () {
    struct timeval tv;
    (void) gettimeofday(&tv, NULL);
    return (double)(tv.tv_sec) + (double)(tv.tv_usec) / 1.0e6;
}

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

	if (file_sz > 0 && file_sz <= 4096) {
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
			printf("hehehehehehehhehehhe %d / %d\n", i, pbuf_write->len);
			printf("Writing %d bytes of data\n", len + 4);
			print_hex(send_buf, len + 4);
			fflush(stdout);
			int ret = write(fd, (const void *) send_buf, len + 4);
			if (ret < 0) {
				perror("Error");
				return -1;
			}
		}
		i += len;
	}

	return 0;
}

int
main (int argc, char **argv)
{
	if (argc != 3 && argc != 4) {
		printf("Version " DIAG_REVEALER_VERSION "\n");
		printf("Usage: diag_revealer DIAG_CFG_PATH FIFO_PATH [QMDL_OUTPUT_PATH]\n");
        return 0;
	}

	BinaryBuffer buf_write = read_diag_cfg(argv[1]);
	if (buf_write.p == NULL || buf_write.len == 0) {
		return -8001;
	}
	// print_hex(buf_write.p, buf_write.len);

	int fd = open("/dev/diag", O_RDWR);
	if (fd < 0) {
		perror("open diag dev");
		return -8002;
	}

	int mode = CALLBACK_MODE;
	// int ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, (char *) mode);
	int ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, (char *) mode);
	if (ret != 1) {
		fprintf(stderr, "ioctl SWITCH_LOGGING returns %d\n", ret);
		perror("ioctl SWITCH_LOGGING");
		return -8003;
	}

	// uint16_t device_mask = 0;
	// ret = ioctl(fd, DIAG_IOCTL_REMOTE_DEV, (char *) &device_mask);
	// printf("ioctl REMOTE_DEV ret: %d\n", ret);

	// // Configure realtime streaming mode
	// int i=0;
	// for(i=0;i<NUM_SMD_CONTROL_CHANNELS;i++){

	// 	struct diag_buffering_mode_t diag_buffering_mode;
	// 	diag_buffering_mode.peripheral = i;
	// 	diag_buffering_mode.mode = DIAG_BUFFERING_MODE_STREAMING;
	// 	diag_buffering_mode.high_wm_val = DEFAULT_HIGH_WM_VAL;
	// 	diag_buffering_mode.low_wm_val = DEFAULT_LOW_WM_VAL;

	// 	int ret = ioctl(fd,DIAG_IOCTL_PERIPHERAL_BUF_CONFIG,(char *) &diag_buffering_mode);
	// 	if(ret != 1)
	// 		perror("ioctl DIAG_IOCTL_PERIPHERAL_BUF_CONFIG");

	// }

	// {
	// 	char ioarg = MODEM_DATA;
	// 	ret = ioctl(fd, DIAG_IOCTL_PERIPHERAL_BUF_DRAIN, (char *) &ioarg);
	// 	if(ret != 1)
	// 		perror("ioctl DIAG_IOCTL_PERIPHERAL_BUF_DRAIN");
	// }

	{
		struct real_time_query_t ioarg;
		ioarg.real_time = -666;
		ioarg.proc = 1000;
		ret = ioctl(fd, DIAG_IOCTL_GET_REAL_TIME, (char *) &ioarg);
		perror("ioctl DIAG_IOCTL_GET_REAL_TIME");
		printf ("ioctl DIAG_IOCTL_GET_REAL_TIME returns %d\n", ret);
		printf ("real_time = %d\n", ioarg.real_time);
	}

	printf("Before write_commands\n");
	ret = write_commands(fd, &buf_write);
	printf("After write_commands\n");
	fflush(stdout);
	free(buf_write.p);
	if (ret != 0) {
		return -8004;
	}

	int fifo_fd = open(argv[2], O_WRONLY);	// block until the other end also calls open()
	FILE *qmdl_fp = NULL;
	if (argc == 4) {
		qmdl_fp = fopen(argv[3], "wb");
		if (qmdl_fp == NULL) {
			perror("open qmdl");
			return -8005;
		}
	}
	printf("Hehe\n");
	while (1) {
		int read_len = read(fd, buf_read, sizeof(buf_read));
		if (read_len > 0) {
			if (*((int *)buf_read) == USER_SPACE_DATA_TYPE) {
				int num_data = *((int *)(buf_read + 4));
				int i = 0;
				int offset = 8;
				for (i = 0; i < num_data; i++) {
					int msg_len;
					double ts = get_posix_timestamp();
					memcpy(&msg_len, buf_read + offset, 4);
					printf("%d %.5f\n", msg_len, ts);
					// print_hex(buf_read + offset + 4, msg_len);
					// Write size of payload to pipe
					write(fifo_fd, &msg_len, sizeof(int));
					// Write timestamp of sending payload to pipe
					write(fifo_fd, &ts, sizeof(double));
					// Write payload to pipe
					write(fifo_fd, buf_read + offset + 4, msg_len);
					// Write qmdl output if necessary
					if (qmdl_fp != NULL) {
						fwrite(buf_read + offset + 4, sizeof(char), msg_len, qmdl_fp);
					}
					offset += msg_len + 4;
				}
			}
		} else {
			continue;
		}
	}

	close(fd);
	// clsoe(fifo_fd);
	return (ret < 0? ret: 0);
}
