# Compiler definitions
CC = gcc
CXX = g++

# Common flags
COMMON_FLAGS = -O3 -ffast-math -Iinclude -I.
CFLAGS = $(COMMON_FLAGS)
CXXFLAGS = $(COMMON_FLAGS)

# Platform-specific settings
ifeq ($(OS),Windows_NT)
    RM = del /Q
    EXEC_EXT = .exe
    LDFLAGS = -lstdc++
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        RM = rm -f
        EXEC_EXT =
        LDFLAGS = -lstdc++
    else
        # Assume Linux or Unix
        RM = rm -f
        EXEC_EXT =
        LDFLAGS = -lstdc++
    endif
endif

# Source files
SRC_C = engine.c nnue_eval.c
SRC_CPP = nnue/nnue.cpp nnue/misc.cpp
OBJ_C = $(SRC_C:.c=.o)
OBJ_CPP = $(SRC_CPP:.cpp=.o)
OBJ = $(OBJ_C) $(OBJ_CPP)

# Output target
TARGET = engine$(EXEC_EXT)

# Build target
all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

# Compilation rules
%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# Clean rule
clean:
	$(RM) $(OBJ) $(TARGET)
