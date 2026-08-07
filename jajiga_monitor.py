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

        await page.wait_for_timeout(5000)

        print("Page loaded")

        # ------------------------------------------------
        # پیدا کردن تمام عناصر مربوط به عدد 28
        # ------------------------------------------------

        print("Searching for day 28...")

        elements_28 = page.get_by_text(
            "۲۸",
            exact=True
        )

        count_28 = await elements_28.count()

        print("Number of elements containing 28:", count_28)

        for i in range(count_28):

            try:

                element = elements_28.nth(i)

                print(
                    "28 element",
                    i,
                    "visible:",
                    await element.is_visible()
                )

            except Exception as e:

                print("Error:", e)

        # ------------------------------------------------
        # screenshot
        # ------------------------------------------------

        await page.screenshot(
            path="calendar_test.png",
            full_page=True
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
