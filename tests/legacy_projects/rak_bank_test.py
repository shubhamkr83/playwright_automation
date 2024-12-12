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
rb = config["RAK_BANK"]


correct_email = os.getenv("RAK_BANK_EMAIL")
correct_password = os.getenv("RAK_BANK_PASSWORD")


# Rak Bank test cases
RB_TEST_CASES = [
    ("profile", "Profile", rb["profile"]),
    ("play_now", "Play Now", rb["play_now"]),
    # ("past_games", "Past Games", rb["past_games"]),
    ("past_lessons", "Past Lessons", rb["past_lessons"]),
]

SELECTORS = {
    "rak_bank": {
        "email_input": "//div[@class='input-group ']//input[@id='email_id']",
        "password_input": "//input[@id='password']",
        "submit_btn": "//button[normalize-space()='Login']",
        "login_success": "//a[normalize-space()='Profile']",
        "incorrect_msg": "Invalid email-id or password",
        "invalid_email_msg": "Please enter a valid email address.",
        "alert_locator": "span.error",
    },
}

PROJECT = "Rak Bank"


async def rak_bank(results):

    # --------------------------------------rak_bank--------------------------------------
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            results.append({"Project Name": PROJECT})
            print(f"Project Name: {PROJECT}")

            page_load_successful = await page_load_check(
                page, PROJECT, rb["home"], results
            )
            if page_load_successful:
                await url_check(page, PROJECT, "Login", rb["home"], results)

                # Check Login Scenarios
                login_successful = await login_tests(
                    page,
                    PROJECT,
                    results,
                    correct_email,
                    correct_password,
                    SELECTORS["rak_bank"]["email_input"],
                    SELECTORS["rak_bank"]["password_input"],
                    SELECTORS["rak_bank"]["submit_btn"],
                    SELECTORS["rak_bank"]["login_success"],
                    SELECTORS["rak_bank"]["incorrect_msg"],
                    SELECTORS["rak_bank"]["alert_locator"],
                )

                # Only proceed with redirection checks if login tests passed
                if login_successful:

                    print("Login successful, proceeding with redirection checks.")

                    # Check redirection for each test case
                    for selector_name, test_name, expected_url in RB_TEST_CASES:
                        time.sleep(TEST_CASE_INTERVAL)
                        await redirection_check(
                            page,
                            PROJECT,
                            "rb",
                            selector_name,
                            test_name,
                            expected_url,
                            results,
                        )

                    await page.locator("a[role='button']").click()
                    await logout_check(
                        page,
                        PROJECT,
                        "rb",
                        SELECTORS["rak_bank"]["submit_btn"],
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
                "Test Cases": "Skipped Rak Bank All Tests Case",
                "Error": format_error_message(e),
            }
        )
    finally:
        await browser.close()

    # return results
