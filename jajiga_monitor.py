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

        # -----------------------------------------
        # انتخاب 4 نفر
        # -----------------------------------------

        guest_input = page.locator(
            '[data-test="room-booking-guests"]'
        )

        await guest_input.click()

        option = page.get_by_text(
            "4 نفر",
            exact=True
        )

        for i in range(await option.count()):

            if await option.nth(i).is_visible():

                await option.nth(i).click()
                break

        await page.wait_for_timeout(1000)

        print("Selected: 4 نفر")

        # -----------------------------------------
        # بررسی عناصر دارای data-test
        # -----------------------------------------

        print("\n===== DATA-TEST ELEMENTS =====")

        elements = page.locator(
            "[data-test]"
        )

        count = await elements.count()

        print(
            "Count:",
            count
        )

        for i in range(count):

            try:

                el = elements.nth(i)

                data_test = await el.get_attribute(
                    "data-test"
                )

                text = (
                    await el.inner_text()
                ).strip()

                if (
                    text
                    or
                    "price" in data_test.lower()
                    or
                    "booking" in data_test.lower()
                    or
                    "total" in data_test.lower()
                ):

                    print(
                        f"\n{i}:"
                    )

                    print(
                        "data-test:",
                        data_test
                    )

                    print(
                        "text:",
                        repr(text[:500])
                    )

            except Exception:
                pass

        # -----------------------------------------
        # بررسی اعداد بزرگ داخل صفحه
        # -----------------------------------------

        print(
            "\n===== PRICE-LIKE ELEMENTS ====="
        )

        spans = page.locator(
            "span"
        )

        count = await spans.count()

        for i in range(count):

            try:

                el = spans.nth(i)

                text = (
                    await el.inner_text()
                ).strip()

                # قیمت‌های احتمالی
                if (
                    "٬" in text
                    and any(
                        c.isdigit()
                        for c in text
                    )
                ):

                    print(
                        f"\nSPAN {i}:",
                        repr(text)
                    )

                    print(
                        "HTML:",
                        (
                            await el.evaluate(
                                "(e) => e.outerHTML"
                            )
                        )[:1500]
                    )

            except Exception:
                pass

        # -----------------------------------------
        # عناصر دارای تومان
        # -----------------------------------------

        print(
            "\n===== TOMAN ELEMENTS ====="
        )

        body = await page.locator(
            "body"
        ).inner_text()

        for line in body.splitlines():

            line = line.strip()

            if "تومان" in line:

                print(
                    repr(line)
                )

        # -----------------------------------------

        await page.screenshot(
            path="four_guests_price.png",
            full_page=True
        )

        print(
            "\nScreenshot saved."
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
