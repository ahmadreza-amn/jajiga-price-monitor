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
                "height": 1200
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

        # =========================================
        # انتخاب 4 نفر
        # =========================================

        guest_input = page.locator(
            '[data-test="room-booking-guests"]'
        )

        print("Guest input count:", await guest_input.count())

        await guest_input.click()

        await page.wait_for_timeout(500)

        options = page.get_by_text(
            "4 نفر",
            exact=True
        )

        selected = False

        for i in range(await options.count()):

            if await options.nth(i).is_visible():

                await options.nth(i).click()

                selected = True

                print("Selected: 4 نفر")

                break

        if not selected:
            print("ERROR: 4 نفر پیدا نشد")

        await page.wait_for_timeout(1000)

        # =========================================
        # انتخاب تاریخ ورود: 28 مرداد
        # =========================================

        print("\nSelecting check-in: 1405-05-28")

        checkin = page.locator(
            '[data-test="calendar-day-1405-05-28"]'
        )

        print(
            "Check-in elements:",
            await checkin.count()
        )

        if await checkin.count() == 0:

            print(
                "ERROR: تاریخ 28 مرداد پیدا نشد"
            )

        else:

            await checkin.first.click()

            print(
                "Check-in selected."
            )

        await page.wait_for_timeout(1000)

        # =========================================
        # انتخاب تاریخ خروج: 30 مرداد
        # =========================================

        print("\nSelecting check-out: 1405-05-30")

        checkout = page.locator(
            '[data-test="calendar-day-1405-05-30"]'
        )

        print(
            "Check-out elements:",
            await checkout.count()
        )

        if await checkout.count() == 0:

            print(
                "ERROR: تاریخ 30 مرداد پیدا نشد"
            )

        else:

            await checkout.first.click()

            print(
                "Check-out selected."
            )

        await page.wait_for_timeout(2000)

        # =========================================
        # نمایش وضعیت تاریخ‌ها
        # =========================================

        print("\n===== DATE INPUTS =====")

        inputs = page.locator(
            "input"
        )

        for i in range(await inputs.count()):

            try:

                el = inputs.nth(i)

                value = await el.input_value()

                placeholder = await el.get_attribute(
                    "placeholder"
                )

                data_test = await el.get_attribute(
                    "data-test"
                )

                print(
                    f"{i}: "
                    f"data-test={data_test} "
                    f"placeholder={placeholder} "
                    f"value={value}"
                )

            except Exception:
                pass

        # =========================================
        # بررسی قیمت‌های صفحه
        # =========================================

        print(
            "\n===== PRICE INFORMATION ====="
        )

        body = await page.locator(
            "body"
        ).inner_text()

        for line in body.splitlines():

            line = line.strip()

            if (
                "تومان" in line
                or "صورتحساب" in line
                or "جمع" in line
                or "هزینه" in line
                or "تخفیف" in line
            ):

                print(
                    repr(line)
                )

        # =========================================
        # بررسی data-test های مربوط به رزرو
        # =========================================

        print(
            "\n===== BOOKING DATA-TEST ====="
        )

        elements = page.locator(
            "[data-test]"
        )

        for i in range(await elements.count()):

            try:

                el = elements.nth(i)

                data_test = await el.get_attribute(
                    "data-test"
                )

               text = (await el.inner_text()).strip().replace("\n", " | ")

                if (
                    "book" in data_test.lower()
                    or
                    "price" in data_test.lower()
                    or
                    "total" in data_test.lower()
                    or
                    "date" in data_test.lower()
                    or
                    "cost" in data_test.lower()
                ):

                    print(
                        f"{data_test}: {text[:500]}"
                    )

            except Exception:
                pass

        # =========================================
        # Screenshot
        # =========================================

        await page.screenshot(
            path="booking_28_29.png",
            full_page=True
        )

        print(
            "\nScreenshot saved: booking_28_29.png"
        )

        print(
            "\n===== FINISHED ====="
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
