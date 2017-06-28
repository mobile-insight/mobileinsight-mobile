#include <errno.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/select.h>
#include <sys/types.h>

#include <android/log.h>
#define  LOG_TAG    "diag_revealer"
#define ANDROID_SOCKET_NAMESPACE_ABSTRACT 0
#define ANDROID_SOCKET_NAMESPACE_RESERVED 1
#define ANDROID_SOCKET_NAMESPACE_FILESYSTEM 2
#define SOCK_STREAM 1
#define LISTEN_BACKLOG 4
#define UNUSED __attribute__((unused))
#define FILESYSTEM_SOCKET_PREFIX "/tmp/"
#define ANDROID_RESERVED_SOCKET_PREFIX "/dev/socket/"
#define SOCKET_NAME_1 "com.mediatek.mdlogger.socket"
#define SOCKET_NAME_2 "com.mediatek.mdlogger.socket1"

#define  LOGE(...)  __android_log_print(ANDROID_LOG_ERROR,LOG_TAG,__VA_ARGS__)
#define  LOGW(...)  __android_log_print(ANDROID_LOG_WARN,LOG_TAG,__VA_ARGS__)
#define  LOGD(...)  __android_log_print(ANDROID_LOG_DEBUG,LOG_TAG,__VA_ARGS__)
#define  LOGI(...)  __android_log_print(ANDROID_LOG_INFO,LOG_TAG,__VA_ARGS__)


int socket_local_client(const char *name, int namespaceId, int type);
int socket_local_client_connect(int fd, const char *name, int namespaceId, int type UNUSED);
int socket_make_sockaddr_un(const char *name, int namespaceId, struct sockaddr_un *p_addr, socklen_t *alen);
void error_msg(const char* str);

int main (int argc, char **argv) {

	char *socketName;
	printf("Trying to connect emdlogger with socketName '%s'\n", SOCKET_NAME_1);
	socketName = SOCKET_NAME_1;
	int socketFd = socket_local_client(socketName, ANDROID_SOCKET_NAMESPACE_ABSTRACT, SOCK_STREAM);
	if (socketFd < 0) {
		printf("Trying to connect emdlogger with socketName '%s'\n", SOCKET_NAME_2);
		socketName = SOCKET_NAME_2;
		socketFd = socket_local_client(socketName, ANDROID_SOCKET_NAMESPACE_ABSTRACT, SOCK_STREAM);
	}
	if (socketFd < 0) error_msg((char*)"ERROR Socket Openning");
	printf("Open socket successfully\n");

	if (argc == 1 || strcmp(argv[1],"-start") == 0){
			printf("Start the emdlogger\n");
			char *start_cmd = "deep_start,2";
			write(socketFd, start_cmd, strlen(start_cmd) + 1);
	}
	if (argc == 1) sleep(10);
	if (argc == 1 || strcmp(argv[1],"-stop") == 0){
			printf("Pause the emdlogger\n");
			char *pause_cmd = "deep_pause";
			write(socketFd, pause_cmd, strlen(pause_cmd) + 1);
	}

	printf("Close the socket\n");
	close(socketFd);
	return 0;
}


void error_msg(const char *str) {
	printf("%s\n", str);
	exit(-1);
}

/**
 * connect to peer named "name"
 * returns fd or -1 on error
 * https://android.googlesource.com/platform/system/core/+/android-4.4_r1/libcutils/socket_local_client.c
 */
int socket_local_client(const char *name, int namespaceId, int type){
    int s = socket(AF_LOCAL, type, 0);
    if(s < 0) {
			printf("Socket Created Fails, Msg: %s\n", strerror(errno));
			return -1;
		}
		if ( 0 > socket_local_client_connect(s, name, namespaceId, type)) {
				printf("Socket Connected Fails, Msg: %s\n", strerror(errno));
        close(s);
        return -1;
    }
    return s;
}

/**
 * connect to peer named "name" on fd
 * returns same fd or -1 on error.
 * fd is not closed on error. that's your job.
 *
 * Used by AndroidSocketImpl
 */
int socket_local_client_connect(int fd, const char *name, int namespaceId, int type UNUSED){
    struct sockaddr_un addr;
    socklen_t alen;
    int err = socket_make_sockaddr_un(name, namespaceId, &addr, &alen);
    if (err < 0) {
			printf("socket_make_sockaddr_un Fails, Msg: %s\n", strerror(errno));
			return -1;
		}
    if(connect(fd, (struct sockaddr *) &addr, alen) < 0) {
			printf("connect Fails, Msg: %s\n", strerror(errno));
			return -1;
		}
    return fd;
}

/* Documented in header file. */
int socket_make_sockaddr_un(const char *name, int namespaceId, struct sockaddr_un *p_addr, socklen_t *alen){

    memset (p_addr, 0, sizeof (*p_addr));
    size_t namelen;

    switch (namespaceId) {
        case ANDROID_SOCKET_NAMESPACE_ABSTRACT:
            namelen  = strlen(name);
            // Test with length +1 for the *initial* '\0'.
            if ((namelen + 1) > sizeof(p_addr->sun_path)) {
							printf("(namelen + 1) > sizeof(p_addr->sun_path)\n");
							return -1;
						}
            /*
             * Note: The path in this case is *not* supposed to be
             * '\0'-terminated. ("man 7 unix" for the gory details.)
             */
            p_addr->sun_path[0] = 0;
            memcpy(p_addr->sun_path + 1, name, namelen);
        		break;

        case ANDROID_SOCKET_NAMESPACE_RESERVED:
            namelen = strlen(name) + strlen(ANDROID_RESERVED_SOCKET_PREFIX);
            /* unix_path_max appears to be missing on linux */
            if (namelen > sizeof(*p_addr)
                    - offsetof(struct sockaddr_un, sun_path) - 1) return -1;
            strcpy(p_addr->sun_path, ANDROID_RESERVED_SOCKET_PREFIX);
            strcat(p_addr->sun_path, name);
        break;

        case ANDROID_SOCKET_NAMESPACE_FILESYSTEM:
            namelen = strlen(name);
            /* unix_path_max appears to be missing on linux */
            if (namelen > sizeof(*p_addr)
                    - offsetof(struct sockaddr_un, sun_path) - 1) return -1;
            strcpy(p_addr->sun_path, name);
        break;
        default:
            // invalid namespace id
            return -1;
    }
    p_addr->sun_family = AF_LOCAL;
    *alen = namelen + offsetof(struct sockaddr_un, sun_path) + 1;
    return 0;
}
