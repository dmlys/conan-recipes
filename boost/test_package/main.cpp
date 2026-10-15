#include <iostream>
#include <boost/chrono.hpp>

int main()
{
	auto now = boost::chrono::system_clock::now();
	std::cout << "boost::chrono::system_clock::now = " << now << std::endl;
	
	return 0;
}