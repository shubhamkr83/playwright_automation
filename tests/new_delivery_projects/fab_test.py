from playwright.async_api import async_playwright
from utils.consts import TEST_CASE_INTERVAL, HEADLESS, CONFIG_PATH_FOR_TEST_FILE
import json, time, os
from utils.util import (
    page_load_check,
    redirection_check,
    login_tests,
    rating_popup_check,
    logout_check,
    format_error_message,
    url_check,
)

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the config.json file dynamically
config_file_path = os.path.join(current_dir, CONFIG_PATH_FOR_TEST_FILE)

with open(config_file_path, "r") as config_file:
    config = json.load(config_file)

# Extract URLs from the config file
fab_conf = config["FAB"]

correct_email = os.getenv("FAB_EMAIL")
correct_password = os.getenv("FAB_PASSWORD")

# FAB test cases
FAB_TEST_CASES = [
    ("dashboard", "Dashboard", fab_conf["dashboard"]),
    ("claim_history", "Claim history", fab_conf["claim_history"]),
    ("profile", "Profile", fab_conf["profile"]),
    ("contact", "Contact", fab_conf["contact"]),
]

SELECTORS = {
    "fab": {
        "email_input": 'input[name="email"]',
        "password_input": 'input[type="password"]',
        "submit_btn": "button.PrimaryButton_button__pdJaq",
        "profile_locator": "(//button[@class='PrimaryButton_button__pdJaq'][normalize-space()='Logout'])[2]",
        "incorrect_msg": "Email/Password entered is incorrect. Please retry or try login via OTP.",
        "alert_locator": "//div[@role='alert']",
    },
}

PROJECT = "FAB"


async def fab(results):

    # ------------ FAB ------------

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            results.append({"Project Name": PROJECT})
            print(f"Project Name: {PROJECT}")

            page_load_successful = await page_load_check(
                page, PROJECT, fab_conf["login"], results
            )

            if page_load_successful:
                await url_check(page, PROJECT, "Login", fab_conf["login"], results)

                # Check Login Scenarios
                login_successful = await login_tests(
                    page,
                    PROJECT,
                    results,
                    correct_email,
                    correct_password,
                    SELECTORS["fab"]["email_input"],
                    SELECTORS["fab"]["password_input"],
                    SELECTORS["fab"]["submit_btn"],
                    SELECTORS["fab"]["profile_locator"],
                    SELECTORS["fab"]["incorrect_msg"],
                    SELECTORS["fab"]["alert_locator"],
                )

                await rating_popup_check(page, "FAB", results)

                # Only proceed with redirection checks if login tests passed
                if login_successful:
                    print("Login successful, proceeding with redirection checks.")

                    # Check redirection for each test case
                    for selector_name, test_name, expected_url in FAB_TEST_CASES:
                        time.sleep(TEST_CASE_INTERVAL)
                        await redirection_check(
                            page,
                            PROJECT,
                            "fab",
                            selector_name,
                            test_name,
                            expected_url,
                            results,
                        )

                    # After checking redirection, check logout
                    await logout_check(
                        page,
                        "FAB",
                        "fab",
                        SELECTORS["fab"]["email_input"],
                        results,
                    )
                else:
                    print("Login tests failed, Skipping redirection and logout checks.")
                    results.append(
                        {
                            "Project Name": PROJECT,
                            "Test Cases": "Login tests, Skipping redirection and logout test cases",
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
        print(f"An error occurred in the FAB test case: {e}")
        results.append(
            {
                "Project Name": PROJECT,
                "Test Cases": "Skipped FAB All Tests Case",
                "Error": format_error_message(e),
            }
        )

    finally:
        await browser.close()
