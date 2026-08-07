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

        # --------------------------------------------
        # متن دکمه‌ها
        # --------------------------------------------

        print("\n===== ALL BUTTONS =====")

        buttons = page.locator("button")
        count = await buttons.count()

        print("Button count:", count)

        for i in range(count):

            try:

                b = buttons.nth(i)

                text = (
                    await b.inner_text()
                ).strip()

                aria = await b.get_attribute(
                    "aria-label"
                )

                title = await b.get_attribute(
                    "title"
                )

                if text or aria or title:

                    print(
                        f"\nBUTTON {i}"
                    )

                    print(
                        "text:",
                        repr(text)
                    )

                    print(
                        "aria:",
                        repr(aria)
                    )

                    print(
                        "title:",
                        repr(title)
                    )

                    print(
                        "HTML:",
                        (
                            await b.evaluate(
                                "(e) => e.outerHTML"
                            )
                        )[:2000]
                    )

            except Exception as e:

                print(
                    "ERROR:",
                    e
                )

        # --------------------------------------------
        # ورودی‌ها
        # --------------------------------------------

        print("\n===== INPUTS =====")

        inputs = page.locator(
            "input, select"
        )

        count = await inputs.count()

        print(
            "Input/select count:",
            count
        )

        for i in range(count):

            try:

                el = inputs.nth(i)

                print(
                    f"\nINPUT {i}"
                )

                print(
                    "tag:",
                    await el.evaluate(
                        "(e) => e.tagName"
                    )
                )

                print(
                    "type:",
                    await el.get_attribute(
                        "type"
                    )
                )

                print(
                    "name:",
                    await el.get_attribute(
                        "name"
                    )
                )

                print(
                    "placeholder:",
                    await el.get_attribute(
                        "placeholder"
                    )
                )

                print(
                    "value:",
                    await el.get_attribute(
                        "value"
                    )
                )

                print(
                    "aria-label:",
                    await el.get_attribute(
                        "aria-label"
                    )
                )

            except Exception as e:

                print(
                    "ERROR:",
                    e
                )

        # --------------------------------------------
        # متن اطراف «مهمان»
        # --------------------------------------------

        print("\n===== GUEST TEXT =====")

        body = await page.locator(
            "body"
        ).inner_text()

        lines = body.splitlines()

        for i, line in enumerate(lines):

            if (
                "مهمان" in line
                or
                "نفر" in line
                or
                "بزرگسال" in line
                or
                "کودک" in line
            ):

                start = max(
                    0,
                    i - 3
                )

                end = min(
                    len(lines),
                    i + 5
                )

                print(
                    "\n".join(
                        lines[start:end]
                    )
                )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
