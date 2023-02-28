from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.select import Select

User = get_user_model()


def login_active_user(self):
    password = "Password123!"
    active_user = User.objects.create_user(
        password=password,
        email="test2@gmail.com",
        is_active=True,
        has_valid_password=True,
        is_superuser=True,
    )

    self.selenium.get("{}{}".format(self.live_server_url, "/accounts/login/"))
    username_input = self.selenium.find_element(By.NAME, "login")
    username_input.send_keys(active_user.email)
    password_input = self.selenium.find_element(By.NAME, "password")
    password_input.send_keys(password)
    self.selenium.find_element(By.XPATH, '//button[text()="Sign In"]').click()


# TODO: Extract some of this out into a pytest fixture that can be shared across tests
class BrowserTests(StaticLiveServerTestCase):
    """
    Group fixture created via this command:
    ./manage.py dumpdata --natural-foreign --natural-primary auth.group > group.json
    """

    fixtures = ["fixtures/group.json"]

    # TODO: Needs to be headless to run on CI. Valuable to run non-headless locally?
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        opts = FirefoxOptions()
        opts.add_argument("--headless")

        cls.selenium = WebDriver(options=opts)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def setUpTestData(cls):
        cls.fixtures = ["group.json", "permission.json"]

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_user_create_form(self):
        login_active_user(self)

        self.selenium.get("{}{}".format(self.live_server_url, reverse("users:create")))

        assert "Create a New User" in self.selenium.title

        select = Select(self.selenium.find_element(By.ID, "id_group"))

        facility_restrictions_dropdown = self.selenium.find_element(
            By.NAME, "facility_restrictions"
        )
        location_restrictions_dropdown = self.selenium.find_element(
            By.NAME, "location_restrictions"
        )

        national_access_radio = self.selenium.find_element(
            By.XPATH, '//input[@value="national"]'
        )
        location_specific_radio = self.selenium.find_element(
            By.XPATH, '//input[@value="location-specific"]'
        )

        # Before a role is chosen
        assert not facility_restrictions_dropdown.is_displayed()
        assert not location_restrictions_dropdown.is_displayed()
        assert not national_access_radio.is_displayed()
        assert not location_specific_radio.is_displayed()

        # When Field Workers role is chosen
        select.select_by_visible_text("Field Workers")

        assert facility_restrictions_dropdown.is_displayed()
        assert not location_restrictions_dropdown.is_displayed()
        assert not national_access_radio.is_displayed()
        assert not location_specific_radio.is_displayed()

        # When Admins role is chosen
        select.select_by_visible_text("Admins")

        assert not facility_restrictions_dropdown.is_displayed()
        assert location_restrictions_dropdown.is_displayed()
        assert national_access_radio.is_displayed()
        assert location_specific_radio.is_displayed()
        assert location_specific_radio.is_selected()

        # When Data Viewer role is chosen
        select.select_by_visible_text("Data Viewers")

        assert not facility_restrictions_dropdown.is_displayed()
        assert location_restrictions_dropdown.is_displayed()
        assert national_access_radio.is_displayed()
        assert location_specific_radio.is_displayed()
        assert location_specific_radio.is_selected()

        # When Data Manager role is chosen
        select.select_by_visible_text("Data Managers")

        assert not facility_restrictions_dropdown.is_displayed()
        assert location_restrictions_dropdown.is_displayed()
        assert national_access_radio.is_displayed()
        assert location_specific_radio.is_displayed()
        assert location_specific_radio.is_selected()

        # When National access radio is selected
        national_access_radio.click()
        assert not location_restrictions_dropdown.is_displayed()
