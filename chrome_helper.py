import os
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager

def get_chrome_driver(options=None):
    """
    Returns an initialized undetected_chromedriver.Chrome instance.
    Uses webdriver_manager to download the matching chromedriver executable,
    which bypasses the SSLV3_ALERT_HANDSHAKE_FAILURE error caused by
    undetected_chromedriver's default patcher download endpoint.
    """
    try:
        print("Using webdriver_manager to fetch the correct ChromeDriver...")
        executable_path = ChromeDriverManager().install()
        executable_path = os.path.normpath(executable_path)
    except Exception as e:
        print(f"Failed to fetch via webdriver_manager: {e}")
        executable_path = None

    kwargs = {}
    if options:
        kwargs["options"] = options
        
    if executable_path:
        print(f"Successfully obtained ChromeDriver at: {executable_path}")
        kwargs["driver_executable_path"] = executable_path
    else:
        print("Falling back to undetected_chromedriver auto-download.")
        
    return uc.Chrome(**kwargs)

