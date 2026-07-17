from cloakbrowser import launch

HEADLESS = False
browser = launch(
    headless=HEADLESS,
    args=[
        '--disable-blink-features=AutomationControlled',
        '--no-sandbox',
        '--disable-dev-shm-usage',
    ]
)
page = browser.new_page()   
page.set_extra_http_headers({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
})
page.goto("https://hanime1.com", wait_until='networkidle', timeout=60000)
input("按 Enter 键退出程序并关闭浏览器...")
browser.close()