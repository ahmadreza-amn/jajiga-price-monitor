import asyncio
import re
from playwright.async_api import async_playwright


URL = "https://www.jajiga.com/room/3159346"

CHECKIN = "1405-05-28"
CHECKOUT = "1405-05-30"


def normalize_number(text):
    """استخراج مبلغ از متن تقویم جاجیگا"""

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٬",
        "01234567890123456789,"
    )

    text = text.translate(translation)

    # متن تقویم معمولاً چیزی شبیه:
    # 28
    # 5,000,000
    #
    # بنابراین باید آخرین عدد را برداریم،
    # نه اینکه همه اعداد را به هم بچسبانیم.

    numbers = re.findall(
        r"\d[\d,]*",
        text
    )

    if not numbers:
        return None

    value = numbers[-1]

    value = value.replace(",", "")

    return int(value)


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

        print(
            "Guest input count:",
            await guest_input.count()
        )

        if await guest_input.count() == 0:
            print("ERROR: guest input پیدا نشد")
            await browser.close()
            return

        await guest_input.first.click()

        await page.wait_for_timeout(500)

        options = page.get_by_text(
            "4 نفر",
            exact=True
        )

        selected = False

        for i in range(await options.count()):

            option = options.nth(i)

            if await option.is_visible():

                await option.click()

                selected = True

                print("Selected: 4 نفر")

                break

        if not selected:

            print("ERROR: گزینه 4 نفر پیدا نشد")

            await browser.close()
            return

        await page.wait_for_timeout(1000)

        # =========================================
        # انتخاب ورود: 28 مرداد
        # =========================================

        print(
            f"\nSelecting check-in: {CHECKIN}"
        )

        checkin = page.locator(
            f'[data-test="calendar-day-{CHECKIN}"]'
        )

        print(
            "Check-in elements:",
            await checkin.count()
        )

        if await checkin.count() == 0:

            print("ERROR: تاریخ ورود پیدا نشد")

            await browser.close()
            return

        await checkin.first.click()

        print("Check-in selected.")

        await page.wait_for_timeout(1000)

        # =========================================
        # انتخاب خروج: 30 مرداد
        # =========================================

        print(
            f"\nSelecting check-out: {CHECKOUT}"
        )

        checkout = page.locator(
            f'[data-test="calendar-day-{CHECKOUT}"]'
        )

        print(
            "Check-out elements:",
            await checkout.count()
        )

        if await checkout.count() == 0:

            print("ERROR: تاریخ خروج پیدا نشد")

            await browser.close()
            return

        await checkout.first.click()

        print("Check-out selected.")

        # صبر برای محاسبه صورتحساب
        await page.wait_for_timeout(2500)

        # =========================================
        # استخراج قیمت 28 مرداد
        # =========================================

        day28 = page.locator(
            '[data-test="calendar-day-1405-05-28"]'
        )

        day28_text = ""

        if await day28.count() > 0:

            day28_text = (
                await day28.first.inner_text()
            ).strip()

        price28 = normalize_number(
            day28_text
        )

        # =========================================
        # استخراج قیمت 29 مرداد
        # =========================================

        day29 = page.locator(
            '[data-test="calendar-day-1405-05-29"]'
        )

        day29_text = ""

        if await day29.count() > 0:

            day29_text = (
                await day29.first.inner_text()
            ).strip()

        price29 = normalize_number(
            day29_text
        )

        # =========================================
        # استخراج مجموع صورتحساب
        # =========================================

        body = await page.locator(
            "body"
        ).inner_text()

        total_price = None

        # ابتدا دنبال متن صورتحساب و مبلغ نزدیک آن می‌گردیم
        lines = [
            line.strip()
            for line in body.splitlines()
            if line.strip()
        ]

        for i, line in enumerate(lines):

            if "صورتحساب" in line:

                # چند خط بعد از صورتحساب را بررسی می‌کنیم
                for candidate in lines[i:i + 8]:

                    value = normalize_number(
                        candidate
                    )

                    if value is not None and value >= 100000:

                        # قیمت‌های روزانه را کنار می‌گذاریم
                        if price28 and value == price28:
                            continue

                        if price29 and value == price29:
                            continue

                        total_price = value
                        break

                if total_price:
                    break

        # اگر مجموع پیدا نشد، از جمع دو شب استفاده می‌کنیم
        if total_price is None:

            if price28 is not None and price29 is not None:

                total_price = price28 + price29

        # =========================================
        # گزارش نهایی
        # =========================================

        print(
            "\n========================================"
        )

        print(
            "===== JAJIGA PRICE REPORT ====="
        )

        print(
            "اقامتگاه: ویلا لب دریا در بندرانزلی - کپورچال"
        )

        print(
            "کد: 3159346"
        )

        print(
            "مهمان: 4 نفر"
        )

        print()

        if price28 is not None:

            print(
                f"28 مرداد: {price28:,} تومان"
            )

        else:

            print(
                "28 مرداد: پیدا نشد"
            )

        if price29 is not None:

            print(
                f"29 مرداد: {price29:,} تومان"
            )

        else:

            print(
                "29 مرداد: پیدا نشد"
            )

        print()

        if total_price is not None:

            print(
                f"مجموع دو شب: {total_price:,} تومان"
            )

        else:

            print(
                "مجموع دو شب: پیدا نشد"
            )

        print(
            "========================================"
        )

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

        await browser.close()


if __name__ == "__main__":

    asyncio.run(main())
