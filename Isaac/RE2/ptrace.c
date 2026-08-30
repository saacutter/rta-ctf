// Compile with gcc -shared ptrace.c -o ptrace.so

long ptrace(int request, int pid, void *addr, void *data) {
    return 0;
}