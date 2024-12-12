from playwright.async_api import async_playwright
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import pandas as pd
import os, glob, traceback, requests, datetime, time, boto3, uuid, json, asyncio, os
from tabulate import tabulate
from utils.consts import TEST_CASE_INTERVAL


# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the path to the config.json file dynamically
config_file_path = os.path.join(current_dir, "../config.json")

with open(config_file_path, "r") as config_file:
    config = json.load(config_file)


comms = config["COMMS"]

# Load the environment variables from the .env file
load_dotenv()

wemail = os.getenv("WRONG_EMAIL")
wpassword = os.getenv("WRONG_PASSWORD")
iemail = os.getenv("INVALID_EMAIL")
wphone = os.getenv("WRONG_PHONE")


# Initialize the S3 client
s3 = boto3.client("s3")

ERROR_DESCRIPTIONS = {
    "TimeoutError": "Operation took too long. Check your internet and try again.",
    "ValueError": "Unexpected input value. Verify the inputs.",
    "NoSuchElementException": "Element not found. Check the website for changes.",
    "AssertionError": "Condition not met. Check data or logic.",
    "RequestException": "Network issue. Verify your internet connection.",
}


def get_user_friendly_error(exception):
    error_type = type(exception).__name__
    return ERROR_DESCRIPTIONS.get(error_type, str(exception))


def format_error_message(e):
    user_friendly_message = get_user_friendly_error(e)
    technical_details = str(e)
    error_message = f"{user_friendly_message}. Technical details: {technical_details}"
    return error_message


url_redirection = "URL Redirection Check"
login_check = "Login Check"

locator_error = "Unable to find the locator"
url_error = "Navigation error"


SELECTORS = {
    "brpl": {
        "home": "body > div:nth-child(11) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3)",
        "history": "//div[@class='d-none d-lg-block'][normalize-space()='My Redemption History']",
        "terms": "//div[@class='d-none d-lg-block'][normalize-space()='T&C']",
        "faq": "//div[@class='d-none d-lg-block'][normalize-space()='FAQS']",
        "privacy": "//div[@class='d-none d-lg-block'][normalize-space()='Privacy Policy']",
        "earnpoint": "//div[@class='d-none d-lg-block'][normalize-space()='Earn points']",
        "contact": "//div[@class='d-none d-lg-block'][normalize-space()='Contact Us']",
    },
    "bypl": {
        "home": "body > div:nth-child(12) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3)",
        "history": "//div[@class='d-none d-lg-block'][normalize-space()='My Redemption History']",
        "terms": "//div[@class='d-none d-lg-block'][normalize-space()='T&C']",
        "faq": "//div[@class='d-none d-lg-block'][normalize-space()='FAQS']",
        "privacy": "//div[@class='d-none d-lg-block'][normalize-space()='Privacy Policy']",
        "earnpoint": "//div[@class='d-none d-lg-block'][normalize-space()='Earn points']",
        "contact": "//div[@class='d-none d-lg-block'][normalize-space()='Contact Us']",
        "redeem": "//div[@class='noselect buttonBackgroundStylePrimaryGradient']",
    },
    "fab": {
        "dashboard": "(//a[@class='NavMenu_item__bY9_h'][normalize-space()='My Benefits'])[1]",
        "claim_history": "(//a[@class='NavMenu_item__bY9_h'][normalize-space()='Claimed Benefits'])[1]",
        "profile": "(//a[@class='NavMenu_item__bY9_h'][normalize-space()='Profile'])[1]",
        "contact": "(//a[@class='NavMenu_item__bY9_h'][normalize-space()='Contact'])[1]",
        "logout": "(//button[@class='PrimaryButton_button__pdJaq'][normalize-space()='Logout'])[2]",
    },
    "ei": {
        "home": "//a[normalize-space()='Book Now']",
        "offer_details": "//a[normalize-space()='Offer Details']",
        "manage_booking": "//a[normalize-space()='Manage Bookings']",
        "manage_profile": "//a[normalize-space()='Manage Profile']",
        "profile_drop": "//a[@id='navbarScrollingDropdown']",
        "logout": "//a[normalize-space()='Logout']",
    },
    "mg": {
        "home": "//a[normalize-space()='Dashboard']",
        "about_program": "//a[normalize-space()='About Program']",
        "new_booking": "//a[normalize-space()='New Booking']",
        "faq": "//a[contains(@href,'https://mashreq.golflan.com/faq')]",
        "terms": "//a[contains(@href,'https://mashreq.golflan.com/terms-and-conditions')]",
        "contact": "//a[normalize-space()='Contact Us']",
        "logout": "//a[normalize-space()='Logout']",
    },
    "rb": {
        "home": "//a[normalize-space()='Concierge']",
        "profile": "//a[normalize-space()='Profile']",
        "play_now": "//a[normalize-space()='Play Now']",
        # "past_games": "//a[normalize-space()='Past Games']",
        "past_lessons": "//a[normalize-space()='Past Lessons']",
        "logout_dropdown": "//a[@role='button']",
        "logout_confirm": " ",
        "logout": "//a[normalize-space()='Logout']",
    },
    "mp": {
        "home": "//nav[@class='nav-menu d-none d-lg-block']//a[normalize-space()='My Pass']",
        "history": "//nav[@class='nav-menu d-none d-lg-block']//a[normalize-space()='History']",
        "contact": "//nav[@class='nav-menu d-none d-lg-block']//a[normalize-space()='Contact']",
        "logout": "//div[@class='dropdown-menu show']//a[@class='dropdown-item'][normalize-space()='Logout']",
        "logout_confirm": "//button[@data-dismiss='modal'][normalize-space()='Yes']",
    },
}


# API trigger function on test failure
def trigger_api_on_failure(current_time, test_case_result):

    url = comms["base"]
    headers = {
        "x-Thriwe-Comms-Key": "STAG_COMMS_KEY",
        "Content-Type": "application/json",
    }

    unique_request_id = str(uuid.uuid4())

    payload = {
        "project_id": "THRIWE_DINING_V1",
        "request_id": unique_request_id,
        "event_type": "test_case_alert",
        "channel": "email",
        "to_email": comms["emails"],
        "payload": {
            "bookingDate": current_time,
            "test_case_result": test_case_result,
            # "test_case_error": test_case_error,
        },
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print("API triggered successfully.")
        else:
            print(f"Failed to trigger API. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while triggering API: {e}")


# Add token in the base url
def update_token(project_name, start_index, results):

    service_data = config.get(project_name)
    if not service_data:
        raise ValueError(f"Service {project_name} not found in configuration.")

    base_url = service_data.get("base")
    tokens = service_data.get("tokens", [])

    if not tokens:
        raise ValueError(f"No tokens found for service {project_name}.")

    # Iterate through the tokens starting from start_index
    for index in range(start_index, len(tokens)):
        token = tokens[index]
        full_url = f"{base_url}{token}"

        try:
            # Simulate a request to check if the token works
            response = requests.get(full_url)

            if response.status_code == 200:
                print(f"Token at index {index} worked.")
                return full_url
            else:
                # Log failure if the token does not work
                print(
                    {
                        "Test Cases": f"Token at index {index} failed with status code {response.status_code}"
                    }
                )
                results.append(
                    {
                        "Project Name": project_name,
                        "Test Cases": f"Token {index} failed for {project_name}",
                        "Status": "failed",
                    }
                )

        except requests.RequestException as e:
            # Handle network errors, etc.
            print(f"Error using token {index}: {e}")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": f"Token {index} failed for {project_name}",
                    "Status": "Failed",
                    "Error": e,
                }
            )

    # If none of the tokens work, raise an error
    raise RuntimeError(f"All tokens failed for {project_name}")


async def page_load_check(page, project_name, url: str, results: list):
    # Try to navigate to the URL
    response = await page.goto(url, timeout=60000)

    # Check if a response was received
    if response:
        status_code = response.status

        # Check for success status codes (2xx)
        if 200 <= status_code < 300:
            print(f"Page loaded successfully with Status Code: {status_code}")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": "Page loaded",
                    "Status": "Passed",
                    "Status Code": status_code,
                }
            )
            page_load_passed = True
        else:
            # Server error or client error (4xx or 5xx status codes)
            print(f"Page load failed with Status Code: {status_code}")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": "Page load",
                    "Status": "Failed",
                    "Error": f"Server responded with status code {status_code}",
                    "Status Code": status_code,
                }
            )
            page_load_passed = False
    else:
        # If no response is received
        print("No response received from the server")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": "Page load",
                "Status": "Failed",
                "Error": "No response received",
            }
        )
        page_load_passed = False

    return page_load_passed


# Check url function
async def url_check(page, project_name, name: str, expected_url: str, results: list):
    try:
        await page.wait_for_url(expected_url, timeout=60000)
        current_url = page.url
        if current_url == expected_url:
            print(
                f"Checking the redirection of the {name} button to the {name} URL, status: Passed"
            )
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": f"{url_redirection}: Checking the redirection of the {name} button to the {name} URL",
                    "Status": "Passed",
                }
            )
        else:
            print(
                f"Checking the redirection of the {name} button to the {name} URL, status: Failed"
            )
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": f"{url_redirection}: Checking the redirection of the {name} button to the {name} URL",
                    "Status": "Failed",
                    "Error": f"{name} redirected to {current_url}",
                }
            )

    except Exception as e:
        current_url = page.url
        print(f"Error while checking URL: {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"{url_redirection}: Checking the redirection of the {name} button to the {name} URL",
                "Status": "Failed",
                "Error": f"{url_error} for {name}.\n Expected:- {expected_url}, but navigated to:- {current_url}",
            }
        )


async def redirection_check(
    page,
    project_name,
    project_locators,
    selector_name,
    test_name,
    expected_url,
    results,
):
    try:

        await page.locator(SELECTORS[project_locators][selector_name]).click()
        await url_check(page, project_name, test_name, expected_url, results)
    except Exception as e:
        print(
            f"An error occurred in Checking the clicking of the {test_name} button: {e}"
        )
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"{url_redirection}: Checking the clicking of the {test_name} button",
                "Status": "Failed",
                "Error": f"{locator_error} for {test_name}. Not able to find the {test_name} button locator",
            }
        )


async def alert_check(
    page, project_name, testcase_name, alert_locator, expected_message, results
):
    try:
        # After attempting to log in with wrong email and password
        error_message_locator = page.locator(alert_locator)

        # Wait for the error message to become visible
        await error_message_locator.wait_for(state="visible")

        # Get the text from the error message
        error_message = await error_message_locator.inner_text()

        # print(f"Raw alert text: '{error_message}'")
        alert_msg = " ".join(error_message.split())

        if alert_msg == expected_message:
            print(f"Checking login for {testcase_name}, Status: Passed")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": f"{login_check}: Checking login for {testcase_name}",
                    "Status": "Passed",
                }
            )
        else:
            print(
                f"Checking login for {testcase_name}, Status: Failed: Expected '{expected_message}', but got '{alert_msg}'"
            )
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": f"{login_check}: Checking login for {testcase_name}",
                    "Status": "Failed",
                    "Error": f"Expected message on alert '{expected_message}', but got '{alert_msg}'",
                }
            )
    except Exception as e:
        print(f"Error in login test case for {testcase_name}: {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"{login_check}: Checking alert",
                "Status": "Failed",
                "Error": f"{locator_error} for Alert. Not able to find alert box",
            }
        )


async def login_status_check(page, project_name, profile_locator, results):
    try:
        # Wait for logout button with timeout
        logout_btn = await page.wait_for_selector(
            profile_locator, timeout=5000
        )  # Adjust timeout as needed
        if await logout_btn.is_visible():
            print(
                "Checking Login with correct email and correct password, Status: Passed"
            )
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": f"{login_check}: Checking Login with correct email and correct password",
                    "Status": "Passed",
                }
            )
            return True  # Login successful
        else:
            raise Exception("Logout button not visible")
    except Exception as e:
        print("Checking Login with correct email and correct password, Status: Failed")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"{login_check}: Checking Login with correct email and correct password",
                "Status": "Failed",
                "Error": f"Error in login check: {str(e)}",
            }
        )
        return False  # Login failed


async def rating_popup_check(page, project_name, results):
    try:
        button = await page.wait_for_selector("(//button[@type='button'])[3]")
        await button.click()
        print("Rating Pop-up clicked")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"{login_check}: Checking button click after login (Rating Pop-up):",
                "Status": "Passed",
            }
        )
    except Exception as e:
        print(f"Error in button click after login: {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"{login_check}: Checking button click after login (Rating Pop-up):",
                "Status": "Failed",
                "Error": f"{locator_error} for Rating Pop-up. \n Technical details: {e}",
            }
        )


# -------------------------- Login_Senario_1 --------------------------
async def login_input_click(
    page,
    project_name,
    email,
    password,
    email_input,
    password_input,
    submit_btn,
    results,
):
    try:
        await page.fill(email_input, email)
        await page.click(submit_btn)
        await page.fill(password_input, password)
        await page.click(submit_btn)
    except Exception as e:
        print(f"Error in login with email {email}: {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": "Login: Checking login with credintials",
                "Status": "Failed",
                "Error": f"{locator_error} for input fields",
            }
        )


async def handle_login_scenario(
    page,
    project_name,
    email,
    password,
    scenario_name,
    alert_locator,
    alert_message,
    email_input,
    password_input,
    submit_btn,
    results,
):
    try:
        # Attempt login
        await login_input_click(
            page,
            project_name,
            email,
            password,
            email_input,
            password_input,
            submit_btn,
            results,
        )
        # Check for alert message
        await alert_check(
            page, project_name, scenario_name, alert_locator, alert_message, results
        )
        return True  # Scenario handled successfully
    except Exception as e:
        print(f"Error in test case '{scenario_name}': {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"Checking Login {scenario_name}",
                "Status": "Failed",
                "Error": format_error_message(e),
            }
        )
        return False  # Scenario failed
    finally:
        await page.reload()  # Ensure the page resets after each test case


async def login_tests(
    page,
    project_name,
    results,
    email,
    password,
    email_input,
    password_input,
    submit_btn,
    profile_locator,
    incorrect_msg,
    alert_locator,
):
    all_tests_passed = True

    # Define login scenarios with email, password, and expected alert message
    login_scenarios = [
        (
            wemail,
            wpassword,
            "Wrong email and wrong password (Aim: Not Logged In)",
            incorrect_msg,
        ),
        (
            wemail,
            password,
            "Wrong email and correct password (Aim: Not Logged In)",
            incorrect_msg,
        ),
        (
            email,
            wpassword,
            "Correct email and wrong password (Aim: Not Logged In)",
            incorrect_msg,
        ),
    ]

    # Test each login scenario
    for (
        email_value,
        password_value,
        scenario_name,
        alert_message,
    ) in login_scenarios:
        scenario_passed = await handle_login_scenario(
            page,
            project_name,
            email_value,
            password_value,
            scenario_name,
            alert_locator,
            alert_message,
            email_input,
            password_input,
            submit_btn,
            results,
        )
        if not scenario_passed:
            all_tests_passed = False  # Mark overall test as failed
        time.sleep(TEST_CASE_INTERVAL)

    # Handle successful login
    if all_tests_passed:
        try:
            await page.reload()
            await login_input_click(
                page,
                project_name,
                email,
                password,
                email_input,
                password_input,
                submit_btn,
                results,
            )
            all_tests_passed = await login_status_check(
                page, project_name, profile_locator, results
            )
        except Exception as e:
            print(f"Error in 'Correct email and correct password': {e}")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": f"{login_check}: Login Correct email and correct password",
                    "Status": "Failed",
                    "Error": format_error_message(e),
                }
            )
            all_tests_passed = False

    return all_tests_passed


# -------------------------- Login_Senario_2 --------------------------
async def login_input_click_2(
    page,
    project_name,
    email,
    password,
    email_input,
    password_input,
    submit_btn,
    results,
):
    try:
        await page.fill(email_input, email)
        await page.fill(password_input, password)
        await page.wait_for_timeout(1000)
        await page.click(submit_btn)
    except Exception as e:
        print(f"Error in login with email {email}: {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": "Login: Checking login with credintials",
                "Status": "Failed",
                "Error": f"{locator_error} for input fields",
            }
        )


async def handle_login_scenario_2(
    page,
    project_name,
    email,
    password,
    scenario_name,
    alert_locator,
    alert_message,
    email_input,
    password_input,
    submit_btn,
    results,
):
    try:
        await login_input_click_2(
            page,
            project_name,
            email,
            password,
            email_input,
            password_input,
            submit_btn,
            results,
        )
        await alert_check(
            page, project_name, scenario_name, alert_locator, alert_message, results
        )
        return True
    except Exception as e:
        print(f"Error in test case '{scenario_name}': {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"Checking Login {scenario_name}",
                "Status": "Failed",
                "Error": format_error_message(e),
            }
        )
        return False
    finally:
        await page.reload()


async def login_tests_2(
    page,
    project_name,
    results,
    email,
    password,
    email_input,
    password_input,
    submit_btn,
    profile_locator,
    incorrect_msg,
    alert_locator,
):

    all_tests_passed = True

    # Define login scenarios with email, password, and expected alert message
    login_scenarios = [
        (
            wemail,
            wpassword,
            "Wrong email and wrong password (Aim: Not Logged In)",
            incorrect_msg,
        ),
        (
            wemail,
            password,
            "Wrong email and correct password (Aim: Not Logged In)",
            incorrect_msg,
        ),
        (
            email,
            wpassword,
            "Correct email and wrong password (Aim: Not Logged In)",
            incorrect_msg,
        ),
    ]

    # Test each login scenario
    for (
        email_value,
        password_value,
        scenario_name,
        alert_message,
    ) in login_scenarios:

        scenario_passed = await handle_login_scenario_2(
            page,
            project_name,
            email_value,
            password_value,
            scenario_name,
            alert_locator,
            alert_message,
            email_input,
            password_input,
            submit_btn,
            results,
        )
        if not scenario_passed:
            all_tests_passed = False  # Mark overall test as failed
        time.sleep(TEST_CASE_INTERVAL)

    # Handle successful login
    try:
        await page.reload()
        await login_input_click_2(
            page,
            project_name,
            email,
            password,
            email_input,
            password_input,
            submit_btn,
            results,
        )
        all_tests_passed = await login_status_check(
            page, project_name, profile_locator, results
        )
    except Exception as e:
        print(f"Error in 'Correct email and correct password': {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"{login_check}: Login Correct email and correct password",
                "Status": "Failed",
                "Error": format_error_message(e),
            }
        )
        all_tests_passed = False

    return all_tests_passed


# -------------------------- Phone_Number_Login_Senario --------------------------
async def login_input_click_3(
    page,
    project_name,
    email,
    password,
    phone_input,
    password_input,
    submit_btn,
    results,
):
    try:
        await page.fill(phone_input, email)
        # print(email)
        await page.fill(password_input, password)
        # print(password)
        await page.wait_for_timeout(1000)
        await page.click(submit_btn)
    except Exception as e:
        print(f"Error in login with email {email}: {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": "Login: Checking login with credintials",
                "Status": "Failed",
                "Error": f"{locator_error} for input fields",
            }
        )


async def handle_login_scenario_3(
    page,
    project_name,
    email,
    password,
    scenario_name,
    alert_locator,
    alert_message,
    email_input,
    password_input,
    submit_btn,
    results,
):
    try:
        await login_input_click_3(
            page,
            project_name,
            email,
            password,
            email_input,
            password_input,
            submit_btn,
            results,
        )
        await alert_check(
            page, project_name, scenario_name, alert_locator, alert_message, results
        )
        return True
    except Exception as e:
        print(f"Error in test case '{scenario_name}': {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"Checking Login {scenario_name}",
                "Status": "Failed",
                "Error": format_error_message(e),
            }
        )
        return False
    finally:
        await page.reload()


async def login_tests_3(
    page,
    project_name,
    results,
    email,
    password,
    email_input,
    password_input,
    submit_btn,
    profile_locator,
    incorrect_msg,
    alert_locator,
):

    all_tests_passed = True

    # Define login scenarios with email, password, and expected alert message
    login_scenarios = [
        (
            wphone,
            wpassword,
            "Wrong phone and wrong password (Aim: Not Logged In)",
            incorrect_msg,
        ),
        (
            wphone,
            password,
            "Wrong phone and correct password (Aim: Not Logged In)",
            incorrect_msg,
        ),
        (
            email,
            wpassword,
            "Correct phone and wrong password (Aim: Not Logged In)",
            incorrect_msg,
        ),
    ]

    # Test each login scenario
    for (
        email_value,
        password_value,
        scenario_name,
        alert_message,
    ) in login_scenarios:

        scenario_passed = await handle_login_scenario_3(
            page,
            project_name,
            email_value,
            password_value,
            scenario_name,
            alert_locator,
            alert_message,
            email_input,
            password_input,
            submit_btn,
            results,
        )
        if not scenario_passed:
            all_tests_passed = False  # Mark overall test as failed
        time.sleep(TEST_CASE_INTERVAL)

    # Successful login
    try:
        await page.reload()
        await login_input_click_3(
            page,
            project_name,
            email,
            password,
            email_input,
            password_input,
            submit_btn,
            results,
        )

        all_tests_passed = await login_status_check(
            page, project_name, profile_locator, results
        )
    except Exception as e:
        print(f"Error in 'Correct email and correct password': {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": f"{login_check}: Login Correct email and correct password",
                "Status": "Failed",
                "Error": format_error_message(e),
            }
        )
        all_tests_passed = False

    return all_tests_passed


# ---------------------------------------------------------------------
async def logout_check(
    page,
    project_name,
    selector_project,
    login_locator,
    results,
):
    try:
        await page.wait_for_selector(
            SELECTORS[selector_project]["logout"], state="visible"
        )
        await page.locator(SELECTORS[selector_project]["logout"]).click()

        await page.wait_for_selector(login_locator)

        if await page.locator(login_locator).is_visible():
            print("Checking Logout, Status: Passed")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": "Checking Logout",
                    "Status": "Passed",
                }
            )
        else:
            print("Checking Logout, Status: Failed")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": "Checking Logout",
                    "Status": "Failed",
                }
            )

    except Exception as e:
        print(f"Error in logout: {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": "Checking Logout",
                "Status": "Failed",
                "Error": f"{locator_error} for Login button.",
            }
        )


async def logout_check_2(
    page,
    project_name,
    selector_project,
    login_locator,
    results,
):
    try:
        logout_confirm = page.locator(SELECTORS[selector_project]["logout_confirm"])

        await page.wait_for_selector(
            SELECTORS[selector_project]["logout"], state="visible"
        )
        await page.locator(SELECTORS[selector_project]["logout"]).click()

        if await logout_confirm.is_visible():
            await logout_confirm.click()

        await page.wait_for_selector(login_locator)

        if await page.locator(login_locator).is_visible():
            print("Checking Logout, Status: Passed")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": "Checking Logout",
                    "Status": "Passed",
                }
            )
        else:
            print("Checking Logout, Status: Failed")
            results.append(
                {
                    "Project Name": project_name,
                    "Test Cases": "Checking Logout",
                    "Status": "Failed",
                }
            )

    except Exception as e:
        print(f"Error in logout: {e}")
        results.append(
            {
                "Project Name": project_name,
                "Test Cases": "Checking Logout",
                "Status": "Failed",
                "Error": f"{locator_error} for Login button.",
            }
        )


# Function to write results to an Excel file
# def write_results_to_excel(results, filename="test_results.xlsx"):
#     df = pd.DataFrame(results)
#     df.to_excel(filename, index=False)
#     print(f"Results saved to {filename}")


def write_results_to_txt(current_time, test_results):

    df = pd.DataFrame(test_results)

    # Convert only specific columns to str before filling NaN with "" for better readability
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = df[col].astype(str).fillna("")

    results_list = df.values.tolist()

    headers = df.columns.tolist()

    table_string = tabulate(results_list, headers, tablefmt="grid")

    output_file = f"test_results_{current_time}.txt"

    # Save the tabular format string to the .txt file
    with open(output_file, "w") as f:
        f.write(table_string)

    print(f"Test results saved in {output_file}")


# ---------------------- S3 ----------------------------
def upload_to_s3(
    current_time,
    bucket,
    region,
    file_name=None,
):
    file_path = f"test_results_{current_time}.txt"
    # Create an S3 client with a specific region
    if region:
        s3 = boto3.client("s3", region_name=region)
    else:
        s3 = boto3.client("s3")  # Use default region if none is provided

    if file_name is None:
        # file_name = file_path
        file_name = os.path.basename(file_path)

    try:
        # Upload the file to the specified bucket
        s3.upload_file(file_path, bucket, file_name)
        print(
            f"File {file_path} uploaded on S3 to {bucket}/{file_name} in region {region}"
        )
        return True
    except FileNotFoundError:
        print("The file was not found", file_path)
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except Exception as e:
        print(f"Something went wrong in S3 file upload: {e}")
        return False


def delete_old_files():
    try:
        # os.remove("*.txt")
        for f in glob.glob("*.txt"):
            if f != "requirements.txt":
                os.remove(f)

        pass
    except Exception:
        traceback.print_exc()


def list_to_html(current_time, test_results):
    # Filter out only failed test cases
    failed_test_results = []
    for result in test_results:
        if "Failed" in result.values() or "Error" in result.keys():
            failed_test_results.append(result)

    if failed_test_results:
        # Convert filtered failed results to HTML for better readability
        df = pd.DataFrame(failed_test_results)
        # import pdb

        # pdb.set_trace()
        # df = df.drop("cURL Command", axis=1)
        df.fillna("", inplace=True)

        # Add some CSS to beautify the table
        html_style = """
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                table, th, td {
                    border: 1px solid black;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                caption {
                    font-size: 1.5em;
                    margin: 10px;
                }
            </style>
            """

        # Convert DataFrame to HTML and append the CSS styling
        failed_test_results_html = df.to_html(
            header=True, table_id="table", index=False
        )
        beautified_failed_test_results = f"{html_style}{failed_test_results_html}"

        # Trigger API on failure only with the failed test cases
        trigger_api_on_failure(current_time, str(beautified_failed_test_results))


async def retry_main_function(main_func, max_retries=3, retry_interval=5 * 60):
    retry_count = 0

    while retry_count <= max_retries:
        test_results = await main_func()

        # Check if there are any failed test cases
        failed_test_results = [
            result
            for result in test_results
            if "Failed" in result.values() or "Error" in result.keys()
        ]

        if not failed_test_results:
            # If no failed test cases, return successful results
            return test_results, True

        retry_count += 1
        print(f"Test failed. Retrying {retry_count}/{max_retries}...")

        if retry_count > max_retries:
            # If max retries reached, return failed results
            print("Max retries reached. Proceeding with failure handling.")
            return test_results, False

        # Wait for 5 minutes (or specified retry_interval) before next retry
        print(f"Waiting {retry_interval // 60} minutes before next retry...")
        await asyncio.sleep(retry_interval)
