// Compile with gcc -o create_job create_job.c -O0

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>

extern char **environ;

bool validate_string(char *string) {
    // Filter the user's input
    for (int i = 0; i < strlen(string); i++) {
        if (string[i] == '.' || string[i] == '/' || string[i] == '\\' || string[i] == '~' || string[i] == ';' ||
            string[i] == '|' || string[i] == '&' || string[i] == '(' || string[i] == ')' || string[i] == '\'' || 
            string[i] == '\"' || string[i] == '*' || string[i] == '?' || string[i] == '[' || string[i] == ']') {
            return false;
        }
    }

    return true;
}

int main(void) {
    // Ask the user for a filename
    char filename[100];
    printf("Please enter a name for the job: ");
    fgets(filename, sizeof(filename), stdin);
    filename[strcspn(filename, "\n")] = '\0';

    // Validate the filename provided
    if (!validate_string(filename)) {
        fprintf(stderr, "The job name contains forbidden characters. Please try again.\n");
        exit(EXIT_FAILURE);
    }

    // Construct the file path
    char path[120];
    snprintf(path, sizeof(path), "/var/job_queue/%s", filename);

    // Ensure the job does not already exist
    if (FILE *f = (fopen(path, "r"))) {
        fprintf(stderr, "A job with that name already exists. Please try again.\n");
        fclose(f);
        exit(EXIT_FAILURE);
    }

    // Get the user's note to add
    char note[100];
    printf("Please enter a short description for the job: ");
    fgets(note, sizeof(note), stdin);
    note[strcspn(note, "\n")] = '\0';

    // Validate the note provided
    if (!validate_string(note)) {
        fprintf(stderr, "The note provided contained forbidden characters. Please try again.\n");
        exit(EXIT_FAILURE);
    }

    // Create the command to echo the contents to a file
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "echo \"%s\" > %s && chmod 700 %s", note, path, path);

    // Run the command
    pid_t pid = fork();
    if (pid == 0) {
        execl("/bin/bash", "bash", "-p", "-c", cmd, NULL);
    }

    int status;
    waitpid(pid, &status, 0);
    if (WIFEXITED(status)) {
        printf("Wrote contents to %s\n", path);
    } else {
        printf("Failed to write contents to %s\n", path);
    }

    exit(EXIT_SUCCESS);
}