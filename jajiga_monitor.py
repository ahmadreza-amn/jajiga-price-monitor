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

        # --------------------------------------------------
        # پیدا کردن متن دقیق 28
        # --------------------------------------------------

        locator = page.get_by_text(
            "28",
            exact=True
        )

        count = await locator.count()

        print("\n===== EXACT 28 ELEMENTS =====")
        print("Count:", count)

        for i in range(count):

            element = locator.nth(i)

            try:

                print(f"\n--- ELEMENT {i} ---")

                print(
                    "Visible:",
                    await element.is_visible()
                )

                print(
                    "Tag:",
                    await element.evaluate(
                        "(e) => e.tagName"
                    )
                )

                print(
                    "Text:",
                    await element.inner_text()
                )

                print(
                    "HTML:"
                )

                html = await element.evaluate(
                    "(e) => e.outerHTML"
                )

                print(html)

                # والد مستقیم
                parent = await element.evaluate(
                    "(e) => e.parentElement.outerHTML"
                )

                print(
                    "\nPARENT HTML:"
                )

                print(parent[:3000])

                # والد والد
                grandparent = await element.evaluate(
                    "(e) => e.parentElement.parentElement.outerHTML"
                )

                print(
                    "\nGRANDPARENT HTML:"
                )

                print(grandparent[:5000])

            except Exception as e:

                print(
                    "ERROR:",
                    e
                )

        # --------------------------------------------------
        # پیدا کردن تمام متن‌های اطراف 28 در body
        # --------------------------------------------------

        body_text = await page.locator(
            "body"
        ).inner_text()

        print(
            "\n===== BODY CONTEXT ====="
        )

        positions = []

        start = 0

        while True:

            pos = body_text.find(
                "28",
                start
            )

            if pos == -1:
                break

            positions.append(pos)

            start = pos + 2

        for pos in positions:

            print("\n--------------------")

            print(
                body_text[
                    max(0, pos - 300):
                    pos + 500
                ]
            )

        # --------------------------------------------------

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
