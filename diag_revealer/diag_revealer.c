#include <endian.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
// #include <linux/diagchar.h>

#define USER_SPACE_DATA_TYPE	0x00000020
#define CALLBACK_DATA_TYPE		0x00000080
#define DIAG_IOCTL_SWITCH_LOGGING	7
#define DIAG_IOCTL_REMOTE_DEV		32
// #define CALLBACK_MODE	6
#define DIAG_IOCTL_PERIPHERAL_BUF_CONFIG	35
#define DIAG_BUFFERING_MODE_STREAMING	0
#define DEFAULT_LOW_WM_VAL	15
#define DEFAULT_HIGH_WM_VAL	85
#define NUM_SMD_CONTROL_CHANNELS 4


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

char buf_read[4096] = {};

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
write_commands (int fd, BinaryBuffer *pbuf_write) {
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
			// printf("Writing %d bytes of data\n", len + 4);
			// print_hex(send_buf, len + 4);
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
	if (argc != 3) {
		printf("Usage: diag_revealer [Diag.cfg file] [Fifo file]\n");
        return 0;
	}

	BinaryBuffer buf_write = read_diag_cfg(argv[1]);
	if (buf_write.p == NULL || buf_write.len == 0) {
		return -8001;
	}
	// print_hex(buf_write.p, buf_write.len);

	int fd = open("/dev/diag", O_RDWR);
	if (fd < 0) {
		perror("Error");
		return -8002;
	}

	// int ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, (char *) CALLBACK_MODE);
	int CALLBACK_MODE = 6;
	int ret = ioctl(fd, DIAG_IOCTL_SWITCH_LOGGING, (char *) &CALLBACK_MODE);
	if (ret != 1) {
		fprintf(stderr, "Error: ioctl SWITCH_LOGGING returns %d\n", ret);
		perror("ioctl SWITCH_LOGGING");
		return -8003;
	}

	// uint16_t device_mask = 0;
	// ret = ioctl(fd, DIAG_IOCTL_REMOTE_DEV, (char *) &device_mask);
	// printf("ioctl REMOTE_DEV ret: %d\n", ret);

	//Configure realtime streaming mode
	// int i=0;
	// for(i=0;i<NUM_SMD_CONTROL_CHANNELS;i++){

	// 	struct diag_buffering_mode_t diag_buffering_mode;
	// 	diag_buffering_mode.peripheral = i;
	// 	diag_buffering_mode.mode = DIAG_BUFFERING_MODE_STREAMING;
	// 	diag_buffering_mode.high_wm_val = DEFAULT_HIGH_WM_VAL;
	// 	diag_buffering_mode.low_wm_val = DEFAULT_LOW_WM_VAL;

	// 	int ret = ioctl(fd,DIAG_IOCTL_PERIPHERAL_BUF_CONFIG,(char *) &diag_buffering_mode);

	// 	if(!ret)
	// 		perror("ioctl DIAG_IOCTL_PERIPHERAL_BUF_CONFIG:");

	// }
	

	ret = write_commands(fd, &buf_write);
	free(buf_write.p);
	if (ret != 0) {
		return -8004;
	}

	int fifo_fd = open(argv[2], O_WRONLY);	// block until the other end also calls open()
	// setvbuf(stdout, NULL, _IONBF, -1);	// disable stdout buffer
	while (1) {
		int read_len = read(fd, buf_read, sizeof(buf_read));
		if (read_len > 0) {
			if (*((int *)buf_read) == USER_SPACE_DATA_TYPE) {
				int num_data = *((int *)(buf_read + 4));
				int i = 0;
				int offset = 8;
				for (i = 0; i < num_data; i++) {
					int msg_len;
					memcpy(&msg_len, buf_read + offset, 4);
					// printf("%d\n", msg_len);
					// print_hex(buf_read + offset + 4, msg_len);
					write(fifo_fd, buf_read + offset + 4, msg_len);
					offset += msg_len + 4;
				}
			}
		} else {
			continue;
		}
	}

	close(fd);
	clsoe(fifo_fd);
	return (ret < 0? ret: 0);
}
