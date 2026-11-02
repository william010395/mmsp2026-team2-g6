CC = gcc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic
CPPFLAGS = -D_POSIX_C_SOURCE=200809L -Iinclude -Ivendor
PYTHON ?= python3
ifeq ($(OS),Windows_NT)
EXE = .exe
LDLIBS = -lws2_32 -lwinmm
else ifeq ($(shell uname -s),Darwin)
LDLIBS = -lpthread -lm
else
LDLIBS = -ldl -lpthread -lm
endif
WAV = tests/data/aeueo-16kHz.wav
all: voicelink$(EXE)
build:
	mkdir -p build
build/audio.o: src/audio.c include/audio.h vendor/miniaudio.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@
voicelink$(EXE): src/voicelink.c build/audio.o $(wildcard include/*.h)
	$(CC) $(CPPFLAGS) $(CFLAGS) $< build/audio.o -o $@ $(LDLIBS)
test: all
	$(PYTHON) tests/test_edges.py
	$(PYTHON) tests/run_mock_tests.py "./voicelink$(EXE) send" "./voicelink$(EXE) recv" $(WAV)
test-ref: all
	$(PYTHON) tests/run_mock_tests.py "$(PYTHON) python_ref/voicelink.py send" "./voicelink$(EXE) recv" $(WAV)
	$(PYTHON) tests/run_mock_tests.py "./voicelink$(EXE) send" "$(PYTHON) python_ref/voicelink.py recv" $(WAV)
measure: all
	$(PYTHON) tools/measure.py
slides:
	$(PYTHON) tools/slides.py
clean:
	rm -rf build voicelink voicelink.exe
.PHONY: all test test-ref measure slides clean
