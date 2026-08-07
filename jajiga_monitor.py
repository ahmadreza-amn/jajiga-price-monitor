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

        # ---------------------------------------------
        # فیلد تعداد نفرات
        # ---------------------------------------------

        guest_input = page.locator(
            'input[placeholder="تعداد نفرات را مشخص کنید"]'
        )

        print(
            "Guest input count:",
            await guest_input.count()
        )

        if await guest_input.count() == 0:

            print("Guest input NOT FOUND")

            await browser.close()
            return

        print(
            "Guest input visible:",
            await guest_input.is_visible()
        )

        # کلیک روی فیلد
        await guest_input.click()

        await page.wait_for_timeout(1000)

        print("\n===== AFTER GUEST CLICK =====")

        # ---------------------------------------------
        # متن صفحه بعد از باز شدن منوی مهمان
        # ---------------------------------------------

        body = await page.locator(
            "body"
        ).inner_text()

        lines = body.splitlines()

        for i, line in enumerate(lines):

            if (
                "بزرگسال" in line
                or
                "کودک" in line
                or
                "نوزاد" in line
                or
                "مهمان" in line
                or
                "نفر" in line
                or
                "+" in line
                or
                "−" in line
            ):

                start = max(
                    0,
                    i - 3
                )

                end = min(
                    len(lines),
                    i + 6
                )

                print(
                    "\n".join(
                        lines[start:end]
                    )
                )

        # ---------------------------------------------
        # تمام دکمه‌های جدید
        # ---------------------------------------------

        print("\n===== BUTTONS AFTER GUEST CLICK =====")

        buttons = page.locator("button")

        count = await buttons.count()

        print(
            "Button count:",
            count
        )

        for i in range(count):

            try:

                b = buttons.nth(i)

                text = (
                    await b.inner_text()
                ).strip()

                aria = await b.get_attribute(
                    "aria-label"
                )

                if text or aria:

                    print(
                        f"BUTTON {i}: "
                        f"text={repr(text)} "
                        f"aria={repr(aria)}"
                    )

            except Exception:
                pass

        # ---------------------------------------------
        # HTML مربوط به فیلد مهمان
        # ---------------------------------------------

        print(
            "\n===== GUEST INPUT PARENT ====="
        )

        html = await guest_input.evaluate(
            "(e) => e.parentElement.parentElement.outerHTML"
        )

        print(html[:10000])

        # ---------------------------------------------
        # screenshot
        # ---------------------------------------------

        await page.screenshot(
            path="guest_menu.png",
            full_page=True
        )

        print(
            "\nScreenshot saved: guest_menu.png"
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
