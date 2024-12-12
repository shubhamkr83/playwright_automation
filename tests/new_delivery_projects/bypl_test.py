from playwright.async_api import async_playwright
from utils.consts import TEST_CASE_INTERVAL, HEADLESS, CONFIG_PATH_FOR_TEST_FILE
import json, time, os
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
bypl = config["BYPL"]


# BYPL test cases
BYPL_TEST_CASES = [
    ("home", "Home", bypl["home"]),
    ("history", "History", bypl["history"]),
    ("terms", "Terms", bypl["terms"]),
    ("faq", "FAQ", bypl["faq"]),
    ("privacy", "Privacy", bypl["privacy"]),
    ("earnpoint", "Earnpoint", bypl["earnpoints"]),
    ("contact", "Contact", bypl["contact"]),
    ("redeem", "Redeem", bypl["redeem"]),
]


async def bypl(results):

    # ------------ BYPL ------------

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            print("Project Name: BYPL")
            results.append({"Project Name": "BYPL"})

            bypl_url = update_token("BYPL", 0, results)
            page_load_successful = await page_load_check(
                page, "BYPL", bypl_url, results
            )

            if page_load_successful:
                for selector_name, test_name, expected_url in BYPL_TEST_CASES:
                    time.sleep(TEST_CASE_INTERVAL)
                    await redirection_check(
                        page,
                        "BYPL",
                        "bypl",
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
                        "Project Name": "BYPL",
                        "Test Cases": "Page load",
                        "Status": "Failed",
                        "Error": "Not able to load the Page, Skipping redirection test case",
                    }
                )

    except Exception as e:
        print(f"An error occurred in BYPL Test Case: {e}")
        results.append(
            {
                "Project Name": "BYPL",
                "Test Cases": "Skipped BYPL All Tests Case",
                "Error": format_error_message(e),
            }
        )

    finally:
        await browser.close()
