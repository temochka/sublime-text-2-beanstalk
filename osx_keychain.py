'''
Keychain accessor implementation is mostly taken from Gist plugin:
https://github.com/condemil/Gist
'''

import sublime
from functools import wraps

if sublime.platform() == 'osx':
    def create_keychain_accessor():
        from ctypes import cdll, util, c_uint32, c_int, c_char_p, c_void_p, \
            POINTER, pointer, byref, Structure, string_at
        lib_security = cdll.LoadLibrary(util.find_library('Security'))

        class SecKeychainAttributeInfo(Structure):
            _fields_ = [("count", c_uint32), ("tag", POINTER(c_uint32)),
                        ("format", POINTER(c_uint32))]

        class SecKeychainAttribute(Structure):
            _fields_ = [("tag", c_uint32), ("length",
                        c_uint32), ("data", c_void_p)]

        class SecKeychainAttributeList(Structure):
            _fields_ = [("count", c_uint32), ("attr", POINTER(
                SecKeychainAttribute))]

        PtrSecKeychainAttributeList = POINTER(SecKeychainAttributeList)

        def keychain_get_credentials(account, username=''):
            password = ''
            account_domain = get_account_domain(account)

            password_buflen = c_uint32()
            password_buf = c_void_p()
            item = c_void_p()

            error = lib_security.SecKeychainFindInternetPassword(
                None,  # keychain, NULL = default
                c_uint32(len(account_domain)),  # server name length
                c_char_p(account_domain),      # server name
                c_uint32(0),  # security domain - unused
                None,        # security domain - unused
                c_uint32(
                    0 if not username else len(username)),  # account name length
                None if not username else c_char_p(username),   # account name
                c_uint32(0),  # path name length - unused
                None,        # path name
                c_uint32(0),  # port, 0 = any
                c_int(0),  # kSecProtocolTypeAny
                c_int(0),  # kSecAuthenticationTypeAny
                None,  # returned password length - unused
                None,  # returned password data - unused
                byref(item))  # returned keychain item reference
            if not error:
                info = SecKeychainAttributeInfo(
                    1,  # attribute count
                    pointer(c_uint32(1633903476)),  # kSecAccountItemAttr
                    pointer(c_uint32(6)))  # CSSM_DB_ATTRIBUTE_FORMAT_BLOB

                attrlist_ptr = PtrSecKeychainAttributeList()
                error = lib_security.SecKeychainItemCopyAttributesAndData(
                    item,  # keychain item reference
                    byref(info),  # list of attributes to retrieve
                    None,  # returned item class - unused
                    byref(attrlist_ptr),  # returned attribute data
                    byref(password_buflen),  # returned password length
                    byref(password_buf))  # returned password data

                if not error:
                    try:
                        if attrlist_ptr.contents.count == 1:
                            attr = attrlist_ptr.contents.attr.contents
                            username = string_at(attr.data, attr.length)
                            password = string_at(
                                password_buf.value, password_buflen.value)
                    finally:
                        lib_security.SecKeychainItemFreeAttributesAndData(
                            attrlist_ptr,
                            password_buf)

            if not username or not password:
                return ('', '')
            else:
                return (username, password)

        return keychain_get_credentials
    access_keychain = create_keychain_accessor()


def get_account_domain(account):
    return "%s.beanstalkapp.com" % account


def with_osx_keychain_support(func):
    @wraps(func)
    def wrapper(account):
        username, password = func(account)

        if username and password:
            return (username, password)

        if sublime.platform() == 'osx':
            return access_keychain(account, username)

        return (username, password)
    return wrapper
