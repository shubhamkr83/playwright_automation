from playwright.async_api import async_playwright
import json, os, time
from dotenv import load_dotenv
from utils.consts import TEST_CASE_INTERVAL, HEADLESS, CONFIG_PATH_FOR_TEST_FILE
from utils.util import (
    redirection_check,
    login_tests_2,
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
mg = config["MASHREQ"]


correct_email = os.getenv("MASHREQ_EMAIL")
correct_password = os.getenv("MASHREQ_PASSWORD")


# FAB test cases
MG_TEST_CASES = [
    ("home", "Home", mg["home"]),
    ("about_program", "About", mg["about"]),
    ("new_booking", "Booking", mg["booking"]),
    ("faq", "FAQ", mg["faq"]),
    ("terms", "Terms", mg["terms"]),
    ("contact", "Contact", mg["contact"]),
]

SELECTORS = {
    "mg": {
        "email_input": "//input[@id='login_email']",
        "password_input": "//input[@id='login_password']",
        "submit_btn": "//button[@id='login_btn']",
        "login_success": "//a[normalize-space()='Logout']",
        "incorrect_msg": "Login authentication failed",
        "invalid_email_msg": "Please enter a valid email",
        "alert_locator": "div.text-center.alert-danger#login_form_error",
    },
}

PROJECT = "Mashreq Golflan"


async def mashreq_golflan(results):

    # --------------------------------------Emirates Islamic--------------------------------------
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            results.append({"Project Name": PROJECT})
            print(f"Project Name: {PROJECT}")

            page_load_successful = await page_load_check(
                page, PROJECT, mg["home"], results
            )

            if page_load_successful:
                await url_check(page, PROJECT, "Login", mg["home"], results)

                # Check Login Scenarios
                login_successful = await login_tests_2(
                    page,
                    PROJECT,
                    results,
                    correct_email,
                    correct_password,
                    SELECTORS["mg"]["email_input"],
                    SELECTORS["mg"]["password_input"],
                    SELECTORS["mg"]["submit_btn"],
                    SELECTORS["mg"]["login_success"],
                    SELECTORS["mg"]["incorrect_msg"],
                    SELECTORS["mg"]["alert_locator"],
                )

                # Only proceed with redirection checks if login tests passed
                if login_successful:
                    print("Login successful, proceeding with redirection checks.")

                    # Check redirection for each test case
                    for selector_name, test_name, expected_url in MG_TEST_CASES:
                        time.sleep(TEST_CASE_INTERVAL)
                        await redirection_check(
                            page,
                            PROJECT,
                            "mg",
                            selector_name,
                            test_name,
                            expected_url,
                            results,
                        )

                    # check logout
                    await logout_check(
                        page,
                        PROJECT,
                        "mg",
                        SELECTORS["mg"]["email_input"],
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
