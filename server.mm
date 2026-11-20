#include <string>
#include <iostream>

class HamaServer {
public:
    static std::string getServerName() {
        return "HAMA KEY SERVER";
    }

    static std::string getVersion() {
        return "1.0";
    }

    static void showStatus() {
        std::cout << getServerName() << std::endl;
        std::cout << "Version: " << getVersion() << std::endl;
    }
};
