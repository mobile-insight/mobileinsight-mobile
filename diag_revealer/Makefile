all: diag_revealer

diag_revealer: diag_revealer.c
	arm-linux-androideabi-gcc -pie $^ -o $@

clean:
	rm -r obj/ libs/
	rm diag_revealer
