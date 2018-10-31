#include <papi.h>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <unistd.h>
#include <math.h>
#include <sys/ptrace.h>
#include <sys/wait.h>

using namespace std;

void handle_error(int x)
{
    cout << "ERROR " << x << endl;
    exit(x);
}

int main(int argc, char** argv)
{
    pid_t pid= fork();
    if(pid == 0)
    {
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        int ret= execl(argv[1], (const char*)argv+1, NULL);
        if(ret < 0)
        {
            cerr << "ERROR ON EXECL" << endl;
        }
    }
    else if(pid > 0)
    {
        int EventSet = PAPI_NULL;
        int retval;

        /* Initialize the PAPI library */
        retval = PAPI_library_init(PAPI_VER_CURRENT);

        if (retval != PAPI_VER_CURRENT)
        {
            fprintf(stderr, "PAPI library init error!\n");
            exit(1);
        }

        /* Create an EventSet */
        if (PAPI_create_eventset(&EventSet) != PAPI_OK)
            handle_error(1);

        /* Add Total Instructions Executed to our EventSet */
        if (PAPI_add_event(EventSet, PAPI_TOT_INS) != PAPI_OK)
            handle_error(1);
        
        /* Add Total Instructions Executed to our EventSet */
        if (PAPI_add_event(EventSet, PAPI_BR_INS) != PAPI_OK)
            handle_error(1);

        if(PAPI_attach(EventSet, pid) != PAPI_OK)
            handle_error(1);

        long long arr[2];
        while(1)
        {
            int status;
            waitpid(pid, &status, 0);
            if (WIFEXITED(status))
                break;

            PAPI_start(EventSet);
            ptrace(PTRACE_CONT, pid, 0, 0);
        }
        PAPI_stop(EventSet, arr);
        PAPI_read(EventSet, arr);
        cout << endl;
        cout << "TOTAL INSTRUCTIONS : " << arr[0] << endl;
        cout << "BRANCH INSTRUCTIONS : " << arr[1] << endl;
    }
}