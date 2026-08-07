
import asyncio
from playwright.async_api import async_playwright


URL = "https://www.jajiga.com/room/3159346"


async def main():

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page(
            viewport={
                "width": 1440,
                "height": 1000
            },
            locale="fa-IR"
        )

        print("Opening Jajiga...")

        await page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Waiting for page...")

        await page.wait_for_timeout(8000)

        print("Page title:")
        print(await page.title())

        print("URL:")
        print(page.url)

        text = await page.locator("body").inner_text()

        print("Page text length:")
        print(len(text))

        print("First 5000 characters:")
        print(text[:5000])

        await page.screenshot(
            path="jajiga_page.png",
            full_page=True
        )

        print("Screenshot saved.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
