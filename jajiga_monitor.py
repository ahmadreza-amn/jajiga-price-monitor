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
        # باز کردن فهرست تعداد نفرات
        # -----------------------------------------

        guest_input = page.locator(
            '[data-test="room-booking-guests"]'
        )

        print(
            "Guest input count:",
            await guest_input.count()
        )

        await guest_input.click()

        await page.wait_for_timeout(500)

        # -----------------------------------------
        # پیدا کردن گزینه 4 نفر
        # -----------------------------------------

        option = page.get_by_text(
            "4 نفر",
            exact=True
        )

        print(
            "4-person options found:",
            await option.count()
        )

        for i in range(await option.count()):

            try:

                print(
                    f"Option {i}: "
                    f"visible="
                    f"{await option.nth(i).is_visible()}"
                )

            except Exception:
                pass

        # -----------------------------------------
        # انتخاب گزینه 4 نفر
        # -----------------------------------------

        visible_option = None

        for i in range(await option.count()):

            if await option.nth(i).is_visible():

                visible_option = option.nth(i)
                break

        if visible_option is None:

            print(
                "ERROR: 4-person option not found"
            )

            await browser.close()
            return

        await visible_option.click()

        await page.wait_for_timeout(1000)

        print(
            "Selected: 4 نفر"
        )

        # -----------------------------------------
        # بررسی مقدار فیلد
        # -----------------------------------------

        value = await guest_input.input_value()

        print(
            "Guest field value:",
            repr(value)
        )

        # -----------------------------------------
        # گرفتن متن بخش رزرو
        # -----------------------------------------

        body = await page.locator(
            "body"
        ).inner_text()

        print(
            "\n===== BOOKING AREA ====="
        )

        lines = body.splitlines()

        for i, line in enumerate(lines):

            if (
                "تاریخ ورود" in line
                or
                "تاریخ خروج" in line
                or
                "تعداد نفرات" in line
                or
                "تومان" in line
                or
                "صورتحساب" in line
            ):

                start = max(
                    0,
                    i - 2
                )

                end = min(
                    len(lines),
                    i + 8
                )

                print(
                    "\n".join(
                        lines[start:end]
                    )
                )

        # -----------------------------------------

        await page.screenshot(
            path="four_guests.png",
            full_page=True
        )

        print(
            "\nScreenshot saved."
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
