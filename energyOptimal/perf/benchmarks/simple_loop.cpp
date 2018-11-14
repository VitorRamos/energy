#include <iostream>
#include <math.h>

using namespace std;

int main()
{
    double x= 0;
    for(int i=1; i<99999; i++)
    {
        for(int j=1; j<99; j++)
        {
            x=pow(i,j)+sqrt(j)*sqrt(j);
        }   
    }
    return x;
}