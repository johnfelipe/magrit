# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
#from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from signal import SIGINT
import psutil
import unittest
import time
from contextlib import closing
from socket import socket, AF_INET, SOCK_STREAM
import os
import sys


RUN_LOCAL = os.environ.get('RUN_TESTS_LOCAL') == 'True'

if RUN_LOCAL:
    browsers = ['Firefox']
else:
    from sauceclient import SauceClient

    USERNAME = os.environ.get('SAUCE_USERNAME')
    ACCESS_KEY = os.environ.get('SAUCE_ACCESS_KEY')
    sauce = SauceClient(USERNAME, ACCESS_KEY)

    browsers = [
        {"platform": "Linux",
         "browserName": "chrome",
         "version": "47"},
#        {"platform": "Windows 8.1",
#         "browserName": "internet explorer",
#         "version": "11"},
        {"platform": "Linux",
         "browserName": "firefox",
         "version": "40"}]


def on_platforms(platforms, local):
    if local:
        def decorator(base_class):
            module = sys.modules[base_class.__module__].__dict__
            for i, platform in enumerate(platforms):
                d = dict(base_class.__dict__)
                d['browser'] = platform
                name = "%s_%s" % (base_class.__name__, i + 1)
                module[name] = type(name, (base_class,), d)
            pass
        return decorator

    def decorator(base_class):
        module = sys.modules[base_class.__module__].__dict__
        for i, platform in enumerate(platforms):
            d = dict(base_class.__dict__)
            d['desired_capabilities'] = platform
            name = "%s_%s" % (base_class.__name__, i + 1)
            module[name] = type(name, (base_class,), d)
    return decorator


def get_port_available(port_nb):
    for available_port in range(port_nb, port_nb + 1000):
        with closing(socket(AF_INET, SOCK_STREAM)) as sock:
            if sock.connect_ex(("0.0.0.0", available_port)) == 0:
                continue
            else:
                return str(available_port)


def setUpModule():
    global p  # Could very likely be changed to avoid global variable
    global port
    port = get_port_available(7878)
    p = psutil.Popen(["noname_app", "--port", port])
    time.sleep(5)


def tearDownModule():
    p.send_signal(SIGINT)
    p.wait(5)
    try:
        p.kill()
    except:
        pass


@on_platforms(browsers, RUN_LOCAL)
class MainFunctionnalitiesTest(unittest.TestCase):
    """
    Runs a test using travis-ci and saucelabs
    """

    def setUp(self):
        if RUN_LOCAL:
            self.setUpLocal()
        else:
            self.setUpSauce()

    def tearDown(self):
        if RUN_LOCAL:
            self.tearDownLocal()
        else:
            self.tearDownSauce()

    def setUpSauce(self):
        self.desired_capabilities['name'] = self.id()
        self.desired_capabilities['tunnel-identifier'] = \
            os.environ['TRAVIS_JOB_NUMBER']
        self.desired_capabilities['build'] = os.environ['TRAVIS_BUILD_NUMBER']
        self.desired_capabilities['tags'] = \
            [os.environ['TRAVIS_PYTHON_VERSION'], 'CI']

        print(self.desired_capabilities)
        self.verificationErrors = []
        self.driver = webdriver.Remote(
            desired_capabilities=self.desired_capabilities,
            command_executor="http://%s:%s@ondemand.saucelabs.com:80/wd/hub" %
            (USERNAME, ACCESS_KEY)
        )
        self.driver.implicitly_wait(10)
        self.base_url = "http://localhost:{}/modules".format(port)
        self.verificationErrors = []
        self.accept_next_alert = True

    def setUpLocal(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(20)
        self.base_url = "http://localhost:{}/modules".format(port)
        self.verificationErrors = []
        self.accept_next_alert = True


    def tearDownLocal(self):
        self.assertEqual([], self.verificationErrors)
        self.driver.quit()

    def tearDownSauce(self):
        self.assertEqual([], self.verificationErrors)
        print("\nLink to your job: \n "
              "https://saucelabs.com/jobs/%s \n" % self.driver.session_id)
        try:
            if sys.exc_info() == (None, None, None):
                sauce.jobs.update_job(self.driver.session_id, passed=True)
            else:
                sauce.jobs.update_job(self.driver.session_id, passed=False)
        finally:
            self.driver.quit()

    def test_stewart(self):
        driver = self.driver
        driver.get(self.base_url)
        if not self.try_element_present(By.ID, "sample_link", 30):
            self.fail("Time out")
        driver.find_element_by_css_selector("#sample_link > b").click()
        Select(driver.find_element_by_css_selector("select.sample_target")
            ).select_by_visible_text("Nuts 3 (2006) European subdivisions (Polygons)")
        Select(driver.find_element_by_css_selector("select.sample_target")
            ).select_by_visible_text("Nuts 2 (2006) European subdivisions (Polygons)")
        driver.find_element_by_xpath("(//button[@type='button'])[2]").click()
        if not self.try_element_present(By.CSS_SELECTOR, "button.swal2-confirm"):
            self.fail("Time out")
        driver.find_element_by_css_selector("button.swal2-confirm.styled").click()
        time.sleep(1)  # Delay for the sweet alert to close
        driver.find_element_by_id("ui-id-3").click()
        driver.find_element_by_id("ui-id-2").click()
        driver.find_element_by_css_selector("img[title=\"Compute stewart potentials...\"]").click()
        time.sleep(0.5)
        driver.find_element_by_id("stewart_nb_class").clear()
        driver.find_element_by_id("stewart_nb_class").send_keys("7")
        driver.find_element_by_id("stewart_span").clear()
        driver.find_element_by_id("stewart_span").send_keys("60")
        Select(driver.find_element_by_id("stewart_mask")).select_by_visible_text("nuts2_data")
        driver.find_element_by_id("stewart_yes").click()
        if not self.try_element_present(By.CSS_SELECTOR, "button.swal2-confirm"):
            self.fail("Time out")
        driver.find_element_by_css_selector("button.swal2-confirm.styled").click()
        time.sleep(1)  # Delay for the sweet alert to close

    def test_cartogram_new_field(self):
        driver = self.driver
        driver.get(self.base_url)
        driver.find_element_by_css_selector("#sample_link > b").click()
        Select(driver.find_element_by_css_selector("select.sample_target")).select_by_visible_text("Nuts 3 (2006) European subdivisions (Polygons)")
        driver.find_element_by_xpath("(//button[@type='button'])[2]").click()
        if not self.try_element_present(By.CSS_SELECTOR, "button.swal2-confirm"):
            self.fail("Time out")
        driver.find_element_by_css_selector("button.swal2-confirm.styled").click()
        time.sleep(1)  # Delay for the sweet alert to close
        driver.find_element_by_id("ui-id-2").click()
        driver.find_element_by_id("browse_button").click()
        time.sleep(1)
        # Test adding fields to the existing table :
        driver.find_element_by_id("add_field_button").click()
        driver.find_element_by_css_selector("input[value=\"NewFieldName\"]").clear()
        driver.find_element_by_css_selector("input[value=\"NewFieldName\"]").send_keys("NewFieldName3")
        # One field based on an operation betweeen two numerical variables :
        Select(driver.find_element_by_css_selector("#field_div1 > select")).select_by_visible_text("gdppps1999")
        Select(driver.find_element_by_xpath("//div[@id='field_div1']/select[3]")).select_by_visible_text("gdppps2008")
        Select(driver.find_element_by_xpath("//div[@id='field_div1']/select[2]")).select_by_visible_text("/")
        driver.find_element_by_xpath("(//button[@type='button'])[4]").click()
        driver.find_element_by_id("add_field_button").click()
        driver.find_element_by_css_selector("input[value=\"NewFieldName\"]").clear()
        driver.find_element_by_css_selector("input[value=\"NewFieldName\"]").send_keys("NewFieldName2")
        # One field based on an operation betweeen a numerical variable and a constant :
        Select(driver.find_element_by_css_selector("#field_div1 > select")).select_by_visible_text("gdppps2008")
        Select(driver.find_element_by_css_selector("#field_div1 > select")).select_by_visible_text("birth_2008")
        Select(driver.find_element_by_css_selector("#field_div1 > select")).select_by_visible_text("gdppps2008")
        Select(driver.find_element_by_xpath("//div[@id='field_div1']/select[2]")).select_by_visible_text("/")
        Select(driver.find_element_by_xpath("//div[@id='field_div1']/select[3]")).select_by_visible_text("Constant value...")
        driver.find_element_by_id("val_opt").clear()
        driver.find_element_by_id("val_opt").send_keys("1000")
        Select(driver.find_element_by_xpath("//div[@id='field_div1']/select[2]")).select_by_visible_text("*")
        driver.find_element_by_xpath("(//button[@type='button'])[4]").click()
        driver.find_element_by_id("add_field_button").click()
        driver.find_element_by_css_selector("input[value=\"NewFieldName\"]").clear()
        driver.find_element_by_css_selector("input[value=\"NewFieldName\"]").send_keys("NewFieldName1")
        # One field based on an operation on a char string field
        Select(driver.find_element_by_id("type_content_select")).select_by_visible_text("Modification on a character field")
        Select(driver.find_element_by_xpath("//div[@id='field_div1']/select[2]")).select_by_visible_text("Truncate")
        driver.find_element_by_id("val_opt").clear()
        driver.find_element_by_id("val_opt").send_keys("2")
        driver.find_element_by_xpath("(//button[@type='button'])[4]").click()
        driver.find_element_by_xpath("//button[@type='button']").click()
        #  Test the dougenik cartogram functionnality...
        driver.find_element_by_css_selector("img[title=\"Render a map using an anamorphose algorythm on a numerical field of your data\"]").click()
        time.sleep(0.5)
        Select(driver.find_element_by_css_selector("select.params")).select_by_visible_text("Dougenik & al. (1985)")
        #  ... using one of these previously computed field :
        Select(driver.find_element_by_id("Anamorph_field")).select_by_visible_text("NewFieldName2")
        driver.find_element_by_id("Anamorph_yes").click()
        if not self.try_element_present(By.CSS_SELECTOR, "button.swal2-confirm"):
            self.fail("Time out")
        driver.find_element_by_css_selector("button.swal2-confirm.styled").click()

    def test_new_field_choro_many_features(self):
        driver = self.driver
        driver.get(self.base_url)
        driver.find_element_by_css_selector("#sample_link > b").click()
        Select(driver.find_element_by_css_selector("select.sample_target")).select_by_visible_text("U.S.A counties (Polygons)")
        driver.find_element_by_xpath("(//button[@type='button'])[2]").click()
        if not self.try_element_present(By.CSS_SELECTOR, "button.swal2-confirm"):
            self.fail("Time out")
        driver.find_element_by_css_selector("button.swal2-confirm.styled").click()
        time.sleep(1)  # Delay for the sweet alert to close
        driver.find_element_by_id("browse_button").click()
        time.sleep(1)
        driver.find_element_by_id("add_field_button").click()
        #  Computing a new field on a layer with more than 3100 features
        #  ... will delegate the operation to the server :
        Select(driver.find_element_by_css_selector("#field_div1 > select")).select_by_visible_text("AWATER")
        Select(driver.find_element_by_xpath("//div[@id='field_div1']/select[2]")).select_by_visible_text("/")
        Select(driver.find_element_by_xpath("//div[@id='field_div1']/select[3]")).select_by_visible_text("ALAND")
        driver.find_element_by_css_selector("input[value=\"NewFieldName\"]").clear()
        driver.find_element_by_css_selector("input[value=\"NewFieldName\"]").send_keys("Ratio")
        driver.find_element_by_xpath("(//button[@type='button'])[4]").click()
        driver.find_element_by_xpath("(//button[@type='button'])[2]").click()
        driver.find_element_by_id("ui-id-2").click()
        driver.find_element_by_css_selector("img[title=\"Render a choropleth map on a numerical field of your data\"]").click()
        time.sleep(0.5)
        #  Let's use this new field to render a choropleth map :
        Select(driver.find_element_by_id("choro_field_1")).select_by_visible_text("Ratio")
        driver.find_element_by_css_selector("option[value=\"Ratio\"]").click()
        driver.find_element_by_id("choro_class").click()
        driver.find_element_by_xpath("(//button[@type='button'])[2]").click()
        driver.find_element_by_id("choro_yes").click()
        driver.find_element_by_id("legend_button").click()
        if not self.try_element_present(By.ID, "legend_root"):
            self.fail("Legeng won't display")

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e:
            return False
        return True

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException as e:
            return False
        return True

    def try_element_present(self, how, what, delay=60):
        for i in range(delay):
            try:
                if self.is_element_present(how, what):
                    return True
            except:
                pass
            time.sleep(1)
        return False

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally:
            self.accept_next_alert = True


if __name__ == "__main__":
    unittest.main()
