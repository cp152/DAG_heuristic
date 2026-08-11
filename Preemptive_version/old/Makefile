CXX := g++
CXXFLAGS := -O2 -std=c++14 -Wall -Werror

ALGO_SRCS := $(wildcard algos/algo-[0-9]*.cpp)
ALGO_EXES := $(patsubst algos/%.cpp,algos/%.exe,$(ALGO_SRCS))
GEN_SRCS := $(wildcard gens/gen*.cpp)
GEN_EXES := $(patsubst gens/%.cpp,gens/%.exe,$(GEN_SRCS))

all: build

build: all.exe sol.exe $(GEN_EXES) $(ALGO_EXES)

all.exe: all.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

$(GEN_EXES): gens/%.exe: gens/%.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

$(ALGO_EXES): algos/%.exe: algos/%.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

sol.exe: sol.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f all.exe sol.exe $(GEN_EXES) $(ALGO_EXES)

.PHONY: all build clean
