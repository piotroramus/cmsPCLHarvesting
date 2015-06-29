
import logging
import netrc

import ldap

def authenticate(login, pwd):

    username = 'cn=%s,ou=users,o=cern,c=ch' % (login.strip(),)
    password = pwd

    logging.debug('request to authenticate request for login %s' % login)
    
    l = ldap.initialize('ldaps://ldap.cern.ch')
    logging.debug('initialised, setting options ... ' )
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, '/etc/openldap/cacerts/CERN_Root_Certification_Authority_2.pem')
    logging.debug('options set ... ' )
    try:
      l.protocol_version = ldap.VERSION3
      logging.debug("ldap setup, binding ... ")
      l.simple_bind_s(username, password)
      valid = True
    except Exception, error:
      raise error
      logging.error("ldap bind for %s returned error: %s " % (username, str(error)))
      return False

    logging.debug("user %s authenticated... " % login )
    return True
    
def userInGroup(login, groupName):

    searchFilter = "cn=%s" % login
    # searchAttribute = ["mail","sAMAccountName"]
    what = ['memberOf']
    
    status, result = search(searchFilter, what)

    if not status:
        logging.error("ldap search for %s/%s returned false " % (searchFilter, what))
        return False

    grpList = [ x.split(',')[0].replace('CN=', '') for x in result[1]['memberOf'] ]
    logging.debug("checking for %s in group %s is %s " % (login, groupName, str(groupName in grpList)) )
    return  groupName in grpList
    
def search(searchFilter, searchAttribute):
    
    l = ldap.initialize('ldaps://xldap.cern.ch')

    basedn = "dc=cern,dc=ch"

    #this will scope the entire subtree under UserUnits
    searchScope = ldap.SCOPE_SUBTREE

    try:    
        ldap_result_id = l.search(basedn, searchScope, searchFilter, searchAttribute)
        result_set = []
        while 1:
            result_type, result_data = l.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                ## if you are expecting multiple results you can append them
                ## otherwise you can just wait until the initial result and break out
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        # print 'search> got:', result_set
    except ldap.LDAPError, e:
        logging.error("ldap search for %s %s returned error: %s " % (searchFilter, searchAttribute, str(e)) )
        l.unbind_s()
        return False, None
        
    l.unbind_s()
    
    return True, result_set[0][0]

def check(login, pwd, groupList):

    if not authenticate(login, pwd):
        print "authentication FAILed for ", login

    print "authentication OK for ", login
    
    for group in groupList:
        if userInGroup(login, group):
            print "user ", login, 'is in group', group
        else:
            print "user ", login, 'is NOT in group', group


def main():
    netRcFile = netrc.netrc()
    (login, account, pwd) = netRcFile.authenticators('ldap.cern.ch')

    check(login, pwd, ['zh', 'zp'])
    check(login, pwd+'ff', ['zh', 'zp'])

if __name__ == '__main__':
    main()
