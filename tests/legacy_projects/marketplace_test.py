from playwright.async_api import async_playwright
import json, os, time
from dotenv import load_dotenv
from utils.consts import TEST_CASE_INTERVAL, HEADLESS, CONFIG_PATH_FOR_TEST_FILE
from utils.util import (
    redirection_check,
    login_tests_3,
    page_load_check,
    logout_check_2,
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
market = config["MARKETPLACE"]


correct_phone = os.getenv("MARKETPLACE_PHONE")
correct_password = os.getenv("MARKETPLACE_PASSWORD")


# FAB test cases
MP_TEST_CASES = [
    ("home", "Home", market["home"]),
    ("history", "History", market["history"]),
    ("contact", "Contact", market["contact"]),
]

SELECTORS = {
    "marketplace": {
        "email_input": "//input[@id='phone']",
        "password_input": "//input[@id='password_for_phone']",
        "submit_btn": "//button[@id='sign_in_btn']",
        "login_success": "//a[@class='get-started-btn scrollto nav-link dropdown-toggle']",
        "incorrect_msg": "Enter Correct & Verified Phone No. & Password or Try with Registered Email Address.",
        "invalid_email_msg": "Please enter a valid email",
        "alert_locator": "//div[@id='sign_in_form_error']",
    },
}

PROJECT = "Marketplace"


async def market_place(results):

    # --------------------------------------Marketplace--------------------------------------
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            results.append({"Project Name": PROJECT})
            print(f"Project Name: {PROJECT}")

            page_load_successful = await page_load_check(
                page, PROJECT, market["home"], results
            )

            if page_load_successful:
                await url_check(page, PROJECT, "Login", market["login"], results)

                # Check Login Scenarios
                login_successful = await login_tests_3(
                    page,
                    PROJECT,
                    results,
                    correct_phone,
                    correct_password,
                    SELECTORS["marketplace"]["email_input"],
                    SELECTORS["marketplace"]["password_input"],
                    SELECTORS["marketplace"]["submit_btn"],
                    SELECTORS["marketplace"]["login_success"],
                    SELECTORS["marketplace"]["incorrect_msg"],
                    SELECTORS["marketplace"]["alert_locator"],
                )

                # Only proceed with redirection checks if login tests passed
                if login_successful:
                    time.sleep(2)
                    print("Login successful, proceeding with redirection checks.")

                    # Check redirection for each test case
                    for selector_name, test_name, expected_url in MP_TEST_CASES:
                        time.sleep(TEST_CASE_INTERVAL)
                        await redirection_check(
                            page,
                            PROJECT,
                            "mp",
                            selector_name,
                            test_name,
                            expected_url,
                            results,
                        )

                    await page.locator(
                        "//nav[@class='nav-menu d-none d-lg-block']//a[@class='get-started-btn scrollto nav-link dropdown-toggle']"
                    ).click()
                    await logout_check_2(
                        page,
                        PROJECT,
                        "mp",
                        SELECTORS["marketplace"]["submit_btn"],
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
                "Test Cases": "Skipped Marketplace All Tests Case",
                "Error": format_error_message(e),
            }
        )
    finally:
        await browser.close()

    # return results
