from playwright.async_api import async_playwright
from utils.consts import HEADLESS, CONFIG_PATH_FOR_TEST_FILE
import json, os
from utils.util import (
    update_token,
    page_load_check,
    url_check,
    format_error_message,
)


# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the config.json file dynamically
config_file_path = os.path.join(current_dir, CONFIG_PATH_FOR_TEST_FILE)

with open(config_file_path, "r") as config_file:
    config = json.load(config_file)

# Extract URLs from the config file
epifi_conf = config["EPIFI"]


async def epifi(results):

    # ------------ EPIFI ------------
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            results.append({"Project Name": "EPIFI"})
            print("Project Name: EPIFI")

            # Open the EPIFI URL
            epifi_url = update_token("EPIFI", 0, results)
            page_load_successful = await page_load_check(
                page, "EPIFI", epifi_url, results
            )

            if page_load_successful:
                # Test Home button redirection
                await url_check(page, "EPIFI", "Home", epifi_conf["home"], results)
            else:
                print("Page load failed")
                results.append(
                    {
                        "Project Name": "EPIFI",
                        "Test Cases": "Page load",
                        "Status": "Failed",
                        "Error": "Not able to load the Page",
                    }
                )

    except Exception as e:
        print(f"An error occurred in the EPIFI Test Case: {e}")
        results.append(
            {
                "Project Name": "EPIFI",
                "Test Cases": "Skipped EPIFI All Tests Case",
                "Error": format_error_message(e),
            }
        )

    finally:
        await browser.close()
