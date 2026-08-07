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
        # تمام متن صفحه
        # --------------------------------------------------

        text = await page.locator("body").inner_text()

        print("\n===== SEARCH RESULTS =====")

        for word in ["۲۸", "28", "مرداد", "1405", "۱۴۰۵"]:

            print(
                f"Searching for [{word}]:",
                text.count(word)
            )

        # --------------------------------------------------
        # عناصر دارای aria-label
        # --------------------------------------------------

        print("\n===== ARIA LABELS =====")

        elements = page.locator("[aria-label]")

        count = await elements.count()

        print("Total aria-label elements:", count)

        for i in range(min(count, 300)):

            try:

                el = elements.nth(i)

                label = await el.get_attribute("aria-label")

                if label:

                    label_normalized = (
                        label
                        .replace("۲", "2")
                        .replace("۸", "8")
                    )

                    if (
                        "28" in label_normalized
                        or
                        "مرداد" in label
                        or
                        "1405" in label
                        or
                        "۱۴۰۵" in label
                    ):

                        print(
                            f"ARIA {i}: {label}"
                        )

            except Exception:
                pass

        # --------------------------------------------------
        # عناصر دارای data-* attributes
        # --------------------------------------------------

        print("\n===== DATA ATTRIBUTES =====")

        elements = page.locator(
            "[data-date], "
            "[data-day], "
            "[data-value], "
            "[data-testid]"
        )

        count = await elements.count()

        print(
            "Potential date elements:",
            count
        )

        for i in range(min(count, 300)):

            try:

                el = elements.nth(i)

                tag = await el.evaluate(
                    "(e) => e.tagName"
                )

                text_value = (
                    await el.inner_text()
                ).strip()

                date_value = (
                    await el.get_attribute(
                        "data-date"
                    )
                )

                day_value = (
                    await el.get_attribute(
                        "data-day"
                    )
                )

                value = (
                    await el.get_attribute(
                        "data-value"
                    )
                )

                testid = (
                    await el.get_attribute(
                        "data-testid"
                    )
                )

                combined = (
                    f"{text_value} "
                    f"{date_value} "
                    f"{day_value} "
                    f"{value} "
                    f"{testid}"
                )

                normalized = (
                    combined
                    .replace("۲", "2")
                    .replace("۸", "8")
                    .replace("۰", "0")
                    .replace("۱", "1")
                    .replace("۴", "4")
                    .replace("۵", "5")
                )

                if (
                    "28" in normalized
                    or
                    "1405" in normalized
                    or
                    "05" in normalized
                ):

                    print(
                        f"{i}: "
                        f"tag={tag}, "
                        f"text={text_value}, "
                        f"date={date_value}, "
                        f"day={day_value}, "
                        f"value={value}, "
                        f"testid={testid}"
                    )

            except Exception:
                pass

        # --------------------------------------------------
        # دکمه‌های تقویم
        # --------------------------------------------------

        print("\n===== BUTTONS =====")

        buttons = page.locator("button")

        count = await buttons.count()

        print("Total buttons:", count)

        for i in range(count):

            try:

                button = buttons.nth(i)

                txt = (
                    await button.inner_text()
                ).strip()

                aria = await button.get_attribute(
                    "aria-label"
                )

                title = await button.get_attribute(
                    "title"
                )

                if txt or aria or title:

                    print(
                        f"BUTTON {i}: "
                        f"text=[{txt}] "
                        f"aria=[{aria}] "
                        f"title=[{title}]"
                    )

            except Exception:
                pass

        # --------------------------------------------------
        # ذخیره HTML صفحه برای بررسی
        # --------------------------------------------------

        html = await page.content()

        with open(
            "jajiga_page.html",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)

        print("\nHTML saved.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
