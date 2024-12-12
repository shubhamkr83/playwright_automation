from playwright.async_api import async_playwright
import json, os, time
from dotenv import load_dotenv
from utils.consts import TEST_CASE_INTERVAL, HEADLESS, CONFIG_PATH_FOR_TEST_FILE
from utils.util import (
    redirection_check,
    login_tests,
    page_load_check,
    logout_check,
    format_error_message,
    url_check,
)

load_dotenv()

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the config.json file dynamically
config_file_path = os.path.join(current_dir, CONFIG_PATH_FOR_TEST_FILE)

with open(config_file_path, "r") as config_file:
    config = json.load(config_file)

# Extract URLs from the config file
ei = config["EIB"]


correct_email = os.getenv("EIB_EMAIL")
correct_password = os.getenv("EIB_PASSWORD")


# FAB test cases
EI_TEST_CASES = [
    ("home", "Home", ei["home"]),
    ("offer_details", "Offer Details", ei["offer_details"]),
    ("manage_booking", "Booking", ei["booking"]),
    ("manage_profile", "Manage Profile", ei["manage_profile"]),
]

SELECTORS = {
    "ei": {
        "email_input": "//input[@id='email']",
        "password_input": "//input[@id='password']",
        "submit_btn": "//button[normalize-space()='Sign In']",
        "login_success": "//a[normalize-space()='Click to proceed']",
        "incorrect_msg": "Invalid Email / Password Combination.",
        "invalid_email_msg": "Please enter a valid email address",
        "alert_locator": "//div[@role='alert']",
    },
}

PROJECT = "Emirates Islamic"


async def emirates_islamic(results):

    # --------------------------------------Emirates Islamic--------------------------------------
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            results.append({"Project Name": PROJECT})
            print(f"Project Name: {PROJECT}")

            page_load_successful = await page_load_check(
                page, PROJECT, ei["home"], results
            )

            if page_load_successful:
                await url_check(page, PROJECT, "Login", ei["home"], results)

                # Check Login Scenarios
                login_successful = await login_tests(
                    page,
                    PROJECT,
                    results,
                    correct_email,
                    correct_password,
                    SELECTORS["ei"]["email_input"],
                    SELECTORS["ei"]["password_input"],
                    SELECTORS["ei"]["submit_btn"],
                    SELECTORS["ei"]["login_success"],
                    SELECTORS["ei"]["incorrect_msg"],
                    SELECTORS["ei"]["alert_locator"],
                )

                # Only proceed with redirection checks if login tests passed
                if login_successful:
                    await page.locator(
                        "//a[normalize-space()='Click to proceed']"
                    ).click()
                    time.sleep(2)
                    print("Login successful, proceeding with redirection checks.")

                    # Check redirection for each test case
                    for selector_name, test_name, expected_url in EI_TEST_CASES:
                        time.sleep(TEST_CASE_INTERVAL)
                        await redirection_check(
                            page,
                            PROJECT,
                            "ei",
                            selector_name,
                            test_name,
                            expected_url,
                            results,
                        )

                    await page.locator("//a[@id='navbarScrollingDropdown']").click()
                    await logout_check(
                        page,
                        PROJECT,
                        "ei",
                        SELECTORS["ei"]["submit_btn"],
                        results,
                    )
                else:
                    print("Login tests failed, Skipping redirection ")
                    results.append(
                        {
                            "Project Name": PROJECT,
                            "Test Cases": "Login tests, Skipping redirection",
                            "Status": "Failed",
                        }
                    )
            else:
                print(
                    "Page load failed, Skipping login,redirection and logout test cases"
                )
                results.append(
                    {
                        "Project Name": PROJECT,
                        "Test Cases": "Page load",
                        "Status": "Failed",
                        "Error": "Not able to load the Page, Skipping login,redirection and logout test cases",
                    }
                )

    except Exception as e:
        print(f"An error occurred in the {PROJECT} test case: {e}")
        results.append(
            {
                "Project Name": PROJECT,
                "Test Cases": "Skipped Emirates Islamic All Tests Case",
                "Error": format_error_message(e),
            }
        )
    finally:
        await browser.close()

    # return results
