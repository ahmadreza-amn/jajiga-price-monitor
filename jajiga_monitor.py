import asyncio
import re

from playwright.async_api import async_playwright


URL = "https://www.jajiga.com/room/3159346"


def normalize_price(text):

    if not text:
        return None

    # تبدیل اعداد فارسی به انگلیسی
    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹",
        "0123456789"
    )

    text = text.translate(table)

    # حذف جداکننده هزارگان
    text = text.replace("٬", "")
    text = text.replace(",", "")
    text = text.replace(" ", "")

    match = re.search(
        r"\d+",
        text
    )

    if not match:
        return None

    return int(match.group())


async def get_day_price(page, date):

    selector = (
        f'[data-test="calendar-day-{date}"]'
    )

    element = page.locator(selector)

    count = await element.count()

    if count == 0:

        print(
            f"DATE NOT FOUND: {date}"
        )

        return None

    # HTML کامل روز
    html = await element.inner_html()

    print(
        f"\nDATE {date}"
    )

    print(
        "HTML:",
        html
    )

    # پیدا کردن span قیمت
    price_elements = element.locator(
        "span"
    )

    count = await price_elements.count()

    for i in range(count):

        text = (
            await price_elements.nth(i).inner_text()
        ).strip()

        price = normalize_price(text)

        if price and price >= 100000:

            print(
                f"PRICE: {price:,} تومان"
            )

            return price

    print(
        "PRICE NOT FOUND"
    )

    return None


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

        print(
            "Opening Jajiga..."
        )

        await page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        await page.wait_for_timeout(
            5000
        )

        print(
            "Page loaded"
        )

        # ----------------------------------------------
        # قیمت 28 مرداد
        # ----------------------------------------------

        price_28 = await get_day_price(
            page,
            "1405-05-28"
        )

        # ----------------------------------------------
        # قیمت 29 مرداد
        # ----------------------------------------------

        price_29 = await get_day_price(
            page,
            "1405-05-29"
        )

        # ----------------------------------------------
        # نتیجه
        # ----------------------------------------------

        print(
            "\n=============================="
        )

        print(
            "Jajiga price report"
        )

        print(
            "Room: 3159346"
        )

        print(
            "Guests: 4"
        )

        print(
            "28 Mordad:",
            f"{price_28:,}"
            if price_28 else
            "NOT FOUND"
        )

        print(
            "29 Mordad:",
            f"{price_29:,}"
            if price_29 else
            "NOT FOUND"
        )

        if price_28 and price_29:

            total = (
                price_28 +
                price_29
            )

            print(
                "------------------------------"
            )

            print(
                "TOTAL:",
                f"{total:,} تومان"
            )

        print(
            "=============================="
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
