#include <stdio.h>
#include <stdlib.h>

int main(void) {
    // Set a restricted PATH
    if (getenv("PATH") == NULL) {
        setenv("PATH", "/bin:/usr/bin", 1);
    }

    // Update the system's packages to the newest versions
    system("apt update");
    system("apt upgrade -y");
}