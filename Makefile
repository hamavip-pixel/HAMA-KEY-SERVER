CXX = clang++
CXXFLAGS = -std=c++17 -Wall -Wextra

all: server

server: server.mm
	$(CXX) $(CXXFLAGS) server.mm -o server

clean:
	rm -f server
