from playwright.async_api import async_playwright
import json, time, os
from utils.consts import TEST_CASE_INTERVAL, HEADLESS, CONFIG_PATH_FOR_TEST_FILE
from utils.util import (
    update_token,
    page_load_check,
    redirection_check,
    format_error_message,
)


# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the config.json file dynamically
config_file_path = os.path.join(current_dir, CONFIG_PATH_FOR_TEST_FILE)

with open(config_file_path, "r") as config_file:
    config = json.load(config_file)

# Extract URLs from the config file
brpl = config["BRPL"]


# BRPL test cases
BRPL_TEST_CASES = [
    ("home", "Home", brpl["home"]),
    ("history", "History", brpl["history"]),
    ("terms", "Terms", brpl["terms"]),
    ("faq", "FAQ", brpl["faq"]),
    ("privacy", "Privacy", brpl["privacy"]),
    ("earnpoint", "Earnpoint", brpl["earnpoints"]),
    ("contact", "Contact", brpl["contact"]),
]


async def brpl(results):

    # ------------ BRPL ------------
    try:

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            print("Project Name: BRPL")
            results.append({"Project Name": "BRPL"})

            brpl_url = update_token("BRPL", 0, results)
            page_load_successful = await page_load_check(
                page, "BRPL", brpl_url, results
            )

            if page_load_successful:
                for selector_name, test_name, expected_url in BRPL_TEST_CASES:
                    time.sleep(TEST_CASE_INTERVAL)
                    await redirection_check(
                        page,
                        "BRPL",
                        "brpl",
                        selector_name,
                        test_name,
                        expected_url,
                        results,
                    )
            else:
                print(
                    "Page load failed, Skipping login,redirection and logout test cases"
                )
                results.append(
                    {
                        "Project Name": "BRPL",
                        "Test Cases": "Page load",
                        "Status": "Failed",
                        "Error": "Not able to load the Page, Skipping redirection test case",
                    }
                )

    except Exception as e:
        print(f"An error occurred in BRPL Test Case: {e}")
        results.append(
            {
                "Project Name": "BRPL",
                "Test Cases": "Skipped BRPL All Tests Case",
                "Error": format_error_message(e),
            }
        )

    finally:
        await browser.close()
