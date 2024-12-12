from playwright.async_api import async_playwright
from tests.legacy_projects.emirates_islamic_test import emirates_islamic
from tests.legacy_projects.mashreq_golflan_test import mashreq_golflan
from tests.legacy_projects.rak_bank_test import rak_bank
from tests.new_delivery_projects.brpl_test import brpl
from tests.new_delivery_projects.bypl_test import bypl
from tests.new_delivery_projects.epifi_test import epifi
from tests.new_delivery_projects.fab_test import fab
from tests.legacy_projects.marketplace_test import market_place
import asyncio, json, datetime, os
from utils.util import (
    # write_results_to_excel,
    write_results_to_txt,
    upload_to_s3,
    list_to_html,
    delete_old_files,
    retry_main_function,
)


# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the config.json file dynamically
config_file_path = os.path.join(current_dir, "config.json")

with open(config_file_path, "r") as config_file:
    config = json.load(config_file)

# Extract URLs from the config file
aws = config["aws"]["s3"]
bucket_name = aws["bucket"]
region = aws["region"]


async def main():
    results = []

    print("___________________ main function starts ______________________")
    # -------------------------- New Delivery Projects ----------------------------
    await brpl(results)

    await bypl(results)

    await epifi(results)

    await fab(results)

    # -------------------------- Legacy Projects ----------------------------

    await emirates_islamic(results)

    await mashreq_golflan(results)

    await rak_bank(results)

    await market_place(results)

    return results


# Looping the main function every 30 minutes
async def run_periodically():
    while True:
        print("Script Starts")
        delete_old_files()

        # Call the retry function for the main test logic
        test_results, success = await retry_main_function(
            main, max_retries=3, retry_interval=5 * 60
        )

        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # If the test failed after all retries, process the test results
        if not success:
            print("Proceeding with failure handling...")

        # Process the test results (whether successful or not)
        list_to_html(current_time, test_results)

        # Optionally write results to a file or other storage
        write_results_to_txt(current_time, test_results)

        # Upload the results to S3 bucket
        upload_to_s3(current_time, bucket_name, region)

        print("Waiting for 30 minutes before next run...")
        await asyncio.sleep(30 * 60)


if __name__ == "__main__":
    # Run the periodic function
    asyncio.run(run_periodically())
