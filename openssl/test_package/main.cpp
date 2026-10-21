#include <iostream>
#include <openssl/opensslv.h>
#include <openssl/provider.h>

int main()
{
	OSSL_PROVIDER * prov = OSSL_PROVIDER_load(nullptr, "default");
	std::cout << "prov ptr = " << prov << std::endl;
	return 0;
}