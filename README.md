# CMS PCL MultiRun Harvesting

In case of _pycurl_ ssl backend problem on lxplus/openstack VM:

`ImportError: pycurl: libcurl link-time ssl backend (nss) is different from compile-time ssl backend (none/other)`

Do the following
```
pip uninstall pycurl
export PYCURL_SSL_LIBRARY=nss
easy_install pycurl
```