# tests/e2e/conftest.py

import subprocess
import time
import pytest
from playwright.sync_api import sync_playwright
import requests
import logging


# add  timestamps and formatting to logger for better readability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# initialize logger
logger = logging.getLogger(__name__)

@pytest.fixture(scope='session')
def fastapi_server():
    """
    Fixture to start the FastAPI server before E2E tests and stop it after tests complete.
    This pretty much sets up the web server
    """
    # Start FastAPI app
    fastapi_process = subprocess.Popen(['python', 'main.py'])
    
    # Define the URL to check if the server is up
    server_url = 'http://127.0.0.1:8000/'
    
    # Wait for the server to start by polling the root endpoint
    timeout = 30  # seconds
    start_time = time.time()
    server_up = False
    
    print("Starting FastAPI server for test")
    logger.info("Starting FastAPI server test ...")
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(server_url)
            if response.status_code == 200:
                server_up = True
                print("FastAPI server is up and running.")
                logger.info("✅ FastAPI test server is up and running at %s", server_url)
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    
    if not server_up:
        fastapi_process.terminate()
        logger.error(f"❌ FastAPI server failed to start within {timeout} seconds")
        raise RuntimeError("FastAPI server failed to start within timeout period.")
    
    yield
    
    # Terminate FastAPI server
    print("Shutting down FastAPI server after Playwright test")
    fastapi_process.terminate()
    fastapi_process.wait()
    print("FastAPI server has been terminated after Playwright test")

@pytest.fixture(scope="session")
def playwright_instance_fixture():
    """
    Fixture to manage Playwright's lifecycle.
    """
    logger.info("Initializing Playwright for test")
    with sync_playwright() as p:
        yield p
    logger.info("Playwright shut down after test")

@pytest.fixture(scope="session")
def browser(playwright_instance_fixture):
    """
    Fixture to launch a browser instance.
    """
    logger.info("Launching Chromium for test")
    browser = playwright_instance_fixture.chromium.launch(headless=True)
    yield browser
    logger.info("Closing Chromium browser for Playwright test")
    browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """
    Fixture to create a new page for each test.
    """
    logger.debug("Opening new browser page after Playwright test")
    page = browser.new_page()
    yield page
    logger.debug("Closing browser page after Playwright test")
    page.close()
