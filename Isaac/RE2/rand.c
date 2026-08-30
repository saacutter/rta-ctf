// Compile with gcc -o rand rand.c -O0

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>

// Hash function "adapted" from https://www.cse.yorku.ca/~oz/hash.html
unsigned long hash(unsigned char *str) {
    unsigned long hash = 5381;
    int c;

    while (c = *str++)
        hash = ((hash << 5) + hash) + c;

    return hash;
}

int main() {
    // If a debugger is detected, stop running
    if (ptrace(PTRACE_TRACEME, 0, 0, 0) < 0) {
        printf("A debugger has been detected. Process terminating.");
        exit(EXIT_FAILURE);
    }

    // Get the password from the user
    char password[50];
    printf("Password: ");
    scanf("%49s", password);

    // Hash the password and convert it to a string
    long hashed = hash(password);
    snprintf(password, sizeof(password), "%ld", hashed);

    // Compare the hash to the correct hash
    const char *correct = "4918347965232805349";
    if (strcmp(password, correct) == 0) {
        // Seed the random number generator using the hashed value
        srand(hashed);

        // XOR the flag bytes to get the hash
        int flag_bytes[] = {0x87, 0x51, 0x7D, 0xF2, 0xAB, 0xB0, 0x88, 0x5D, 0x7A, 0x4C, 0xCB, 0x93, 0x6E, 0x53, 0xE0, 0x18, 0x3C, 0x98, 0x9, 0x66, 0x47, 0x57, 0xED, 0x9A, 0xED, 0xFD, 0x6F, 0x3B, 0x1C, 0x1F, 0xC9, 0x23, 0x61, 0x73, 0x56, 0xF4, 0x16, 0x00, 0xF2, 0xF2};
        char flag[41];
        for (int i = 0; i < 40; i++) {
            flag[i] = (rand() % 255) ^ flag_bytes[i];
        }
        flag[40] = '\0';

        printf("Flag: ");
        printf("%s\n", flag);
    }
}