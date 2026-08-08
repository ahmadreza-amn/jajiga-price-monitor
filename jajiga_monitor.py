import asyncio
import re
import json
import os
from playwright.async_api import async_playwright


URL = "https://www.jajiga.com/room/3159346"

CHECKIN = "1405-05-28"
CHECKOUT = "1405-05-30"

STATE_FILE = "price_state.json"


def load_previous_prices():

    if not os.path.exists(STATE_FILE):

        return {
            "price_28": None,
            "price_29": None,
            "total": None
        }

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {
            "price_28": None,
            "price_29": None,
            "total": None
        }


def save_current_prices(
    price_28,
    price_29,
    total
):

    data = {
        "price_28": price_28,
        "price_29": price_29,
        "total": total
    }

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def format_price(value):

    if value is None:
        return "نامشخص"

    return f"{value:,} تومان"


def compare_prices(
    previous,
    current_28,
    current_29,
    current_total
):

    old_28 = previous.get("price_28")
    old_29 = previous.get("price_29")
    old_total = previous.get("total")

    # اجرای اول است؛ قیمت قبلی نداریم
    if (
        old_28 is None
        or old_29 is None
        or old_total is None
    ):

        print(
            "\nاولین اجرای ربات است؛"
            " قیمت فعلی به عنوان قیمت پایه ذخیره می‌شود."
        )

        return False

    changed = (
        old_28 != current_28
        or old_29 != current_29
        or old_total != current_total
    )

    if not changed:

        print(
            "\nقیمت‌ها نسبت به اجرای قبلی تغییری نکرده‌اند."
        )

        return False

    print(
        "\n🔔 PRICE CHANGE DETECTED"
    )

    print(
        f"مجموع قبلی: {format_price(old_total)}"
    )

    print(
        f"مجموع جدید: {format_price(current_total)}"
    )

    total_difference = current_total - old_total

    if total_difference < 0:

        print(
            f"کاهش قیمت: {format_price(abs(total_difference))}"
        )

    elif total_difference > 0:

        print(
            f"افزایش قیمت: {format_price(total_difference)}"
        )

    print()

    if old_28 != current_28:

        difference_28 = current_28 - old_28

        print(
            f"28 مرداد قدیم: {format_price(old_28)}"
        )

        print(
            f"28 مرداد جدید: {format_price(current_28)}"
        )

        if difference_28 < 0:

            print(
                f"کاهش 28 مرداد: "
                f"{format_price(abs(difference_28))}"
            )

        else:

            print(
                f"افزایش 28 مرداد: "
                f"{format_price(difference_28)}"
            )

    if old_29 != current_29:

        difference_29 = current_29 - old_29

        print(
            f"29 مرداد قدیم: {format_price(old_29)}"
        )

        print(
            f"29 مرداد جدید: {format_price(current_29)}"
        )

        if difference_29 < 0:

            print(
                f"کاهش 29 مرداد: "
                f"{format_price(abs(difference_29))}"
            )

        else:

            print(
                f"افزایش 29 مرداد: "
                f"{format_price(difference_29)}"
            )

    return True

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

    print("ERROR: تاریخ 28 مرداد پیدا نشد")

else:

    checkin_el = checkin.first

    aria_disabled = await checkin_el.get_attribute("aria-disabled")
    aria_label = await checkin_el.get_attribute("aria-label")
    class_name = await checkin_el.get_attribute("class")

    print("Check-in aria-disabled:", aria_disabled)
    print("Check-in aria-label:", aria_label)

    if aria_disabled == "true":

        print("ERROR: تاریخ 28 مرداد توسط جاجیگا غیرفعال شده است.")
        print("aria-label:", aria_label)
        print("class:", class_name)

        # ذخیره HTML برای بررسی
        html = await checkin_el.evaluate(
            "(el) => el.outerHTML"
        )

        print("HTML:")
        print(html)

        await page.screenshot(
            path="calendar_disabled.png",
            full_page=True
        )

        await browser.close()
        return

    await checkin_el.click()

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
        # مقایسه با قیمت قبلی
        # =========================================

        previous_prices = load_previous_prices()

        price_changed = compare_prices(
            previous_prices,
            price28,
            price29,
            total_price
        )

        # ذخیره قیمت فعلی
        save_current_prices(
            price28,
            price29,
            total_price
        )



        
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
