import os, yaml, munch, time, datetime, logging, re
from selenium import webdriver
import munch
from munch import *

class Browser():
    def __init__(self, host,
                 port=443,
                 browser_type='firefox',
                 username='admin',
                 password='admin',
                 waittime=60,
                 captured_dir='/var/www/html/screenshots',
                 captured_url='http://10.78.192.78/screenshots';,
                 yamlfile=None):
        #Attempt to open broswer
        try:
            if browser_type == 'firefox':
                self.driver = webdriver.Firefox()
            elif browser_type == 'chrome':
                self.driver = webdriver.Chrome()
        except Exception as e:
                raise Exception("Unable to open browser: %s" %e)
        # Define variables used throughout class
        self.host = host
        self.port = port
        self.url = '%s:%s' % (host, port)
        self.username = username
        self.password = password
        self.wait = WebDriverWait(self.driver, waittime)
        self.driver.get(self.url)
        self.driver.maximize_window()
        # self._login_()
        
    def _login_(self, user_path, pass_path, logon_path):
        #Confirm on login page
        try:
            self._locate_(self.elms.login.logon)
        except:
            self._raise_exception_("Not able to Login")
        #Send Login data
        self._type_(user_path, self.username)
        self._type_(pass_path, self.password)
        self._locate_(logon_path).click()
        # self.wait.until(EC.title_contains("Title"))
        
    def _locate_(self, by, waittime=60):
        try:
            self.wait = WebDriverWait(self.driver, waittime)
            e = self.find_element(%s)" % by.locator, globals(), _locals)
            return _locals['e']
        except:
            return 0
    def _type_(self, by, keys):
        self._locate_(by).clear()
        self._locate_(by).send_keys(keys)
if __name__=="__main__":
    broswer = 