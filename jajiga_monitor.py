import asyncio
import json
import os
import re
from pathlib import Path

import requests
from playwright.async_api import async_playwright


# =========================================================
# CONFIG
# =========================================================

URL = "https://www.jajiga.com/room/3159346"

ROOM_CODE = "3159346"
ROOM_NAME = "ویلا لب دریا در بندرانزلی - کپورچال"

GUESTS = 4

CHECKIN_DATE = "1405-05-28"
CHECKOUT_DATE = "1405-05-30"

DATE_28 = "1405-05-28"
DATE_29 = "1405-05-29"

STATE_FILE = Path("price_state.json")

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


# =========================================================
# UTILITIES
# =========================================================

def normalize_digits(text):
    """
    تبدیل ارقام فارسی و عربی به انگلیسی
    """

    if not text:
        return ""

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(translation)


def parse_price(text):
    """
    استخراج عدد قیمت از متن‌هایی مثل:

    5٬000٬000
    ۵٬۰۰۰٬۰۰۰
    5,000,000 تومان
    """

    if not text:
        return None

    text = normalize_digits(text)

    # جداکننده‌های فارسی/عربی/انگلیسی
    text = (
        text
        .replace("٬", "")
        .replace(",", "")
        .replace("،", "")
        .replace(" ", "")
        .replace("تومان", "")
    )

    match = re.search(r"\d+", text)

    if not match:
        return None

    return int(match.group())


def format_price(price):
    """
    نمایش قیمت با جداکننده سه‌رقمی
    """

    return f"{price:,}".replace(",", "٬")


def format_change(change):
    """
    نمایش مقدار تغییر
    """

    return format_price(abs(change))


def load_state():
    """
    خواندن قیمت قبلی
    """

    if not STATE_FILE.exists():
        return None

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(
            "WARNING: Could not read state file:",
            e
        )

        return None


def save_state(
    price_28,
    price_29,
    total
):
    """
    ذخیره قیمت فعلی
    """

    data = {
        "room_code": ROOM_CODE,
        "room_name": ROOM_NAME,
        "guests": GUESTS,
        "checkin": CHECKIN_DATE,
        "checkout": CHECKOUT_DATE,
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


# =========================================================
# TELEGRAM
# =========================================================

def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN:
        print(
            "WARNING: TELEGRAM_BOT_TOKEN is not configured."
        )
        return False

    if not TELEGRAM_CHAT_ID:
        print(
            "WARNING: TELEGRAM_CHAT_ID is not configured."
        )
        return False

    api_url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:

        response = requests.post(
            api_url,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        if not result.get("ok"):

            print(
                "Telegram error:",
                result
            )

            return False

        print(
            "Telegram message sent successfully."
        )

        return True

    except Exception as e:

        print(
            "Telegram send error:",
            e
        )

        return False


# =========================================================
# PRICE MESSAGE
# =========================================================

def build_price_change_message(
    old,
    new
):

    total_change = new["total"] - old["total"]

    if total_change < 0:

        direction = "کاهش قیمت"
        amount = format_change(total_change)

    else:

        direction = "افزایش قیمت"
        amount = format_change(total_change)

    message = (
        "🔔 تغییر قیمت جاجیگا\n"
        "\n"
        f"اقامتگاه: {ROOM_NAME}\n"
        f"تاریخ: ۲۸ تا ۳۰ مرداد\n"
        f"مهمان: {GUESTS} نفر\n"
        "\n"
        f"قیمت قبلی: {format_price(old['total'])} تومان\n"
        f"قیمت جدید: {format_price(new['total'])} تومان\n"
        f"{direction}: {amount} تومان\n"
        "\n"
        "━━━━━━━━━━━━━━\n"
        "\n"
        "قیمت‌های شبانه:\n"
        "\n"
        f"قیمت قدیم ۲۸ مرداد: "
        f"{format_price(old['price_28'])} تومان\n"
        f"قیمت جدید ۲۸ مرداد: "
        f"{format_price(new['price_28'])} تومان\n"
        "\n"
        f"قیمت قدیم ۲۹ مرداد: "
        f"{format_price(old['price_29'])} تومان\n"
        f"قیمت جدید ۲۹ مرداد: "
        f"{format_price(new['price_29'])} تومان"
    )

    # تغییر 28 مرداد
    change_28 = (
        new["price_28"] -
        old["price_28"]
    )

    if change_28 != 0:

        if change_28 < 0:

            text_28 = (
                f"کاهش قیمت ۲۸ مرداد: "
                f"{format_price(abs(change_28))} تومان"
            )

        else:

            text_28 = (
                f"افزایش قیمت ۲۸ مرداد: "
                f"{format_price(abs(change_28))} تومان"
            )

        message += "\n" + text_28

    # تغییر 29 مرداد
    change_29 = (
        new["price_29"] -
        old["price_29"]
    )

    if change_29 != 0:

        if change_29 < 0:

            text_29 = (
                f"کاهش قیمت ۲۹ مرداد: "
                f"{format_price(abs(change_29))} تومان"
            )

        else:

            text_29 = (
                f"افزایش قیمت ۲۹ مرداد: "
                f"{format_price(abs(change_29))} تومان"
            )

        message += "\n" + text_29

    return message


# =========================================================
# FIND CALENDAR PRICE
# =========================================================

async def get_calendar_price(
    page,
    date
):

    selector = (
        f'[data-test="calendar-day-{date}"]'
    )

    locator = page.locator(selector)

    count = await locator.count()

    print(
        f"{date} elements:",
        count
    )

    if count == 0:

        return None

    for i in range(count):

        try:

            element = locator.nth(i)

            text = await element.inner_text()

            text = text.strip()

            print(
                f"{date} raw text:",
                repr(text)
            )

            # معمولاً:
            #
            # 28
            # 5٬000٬000
            #
            # یا:
            #
            # 28\n5٬000٬000

            lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            for line in lines:

                normalized = normalize_digits(
                    line
                )

                # حذف عدد روز
                if normalized in (
                    date[-2:].lstrip("0"),
                    date[-2:]
                ):
                    continue

                price = parse_price(line)

                if price is not None:

                    # قیمت‌های بسیار کوچک را قیمت اجاره در نظر نمی‌گیریم
                    if price >= 100000:

                        print(
                            f"PRICE FOUND {date}: "
                            f"{format_price(price)}"
                        )

                        return price

        except Exception as e:

            print(
                f"WARNING reading {date}:",
                e
            )

    return None


# =========================================================
# MAIN
# =========================================================

async def main():

    print(
        "========================================"
    )

    print(
        "===== JAJIGA PRICE MONITOR ====="
    )

    print(
        "========================================"
    )

    browser = None

    try:

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

            # =================================================
            # انتخاب 4 نفر
            # =================================================

            guest_input = page.locator(
                '[data-test="room-booking-guests"]'
            )

            guest_count = await guest_input.count()

            print(
                "Guest input count:",
                guest_count
            )

            if guest_count == 0:

                raise Exception(
                    "Guest input not found."
                )

            await guest_input.first.click()

            await page.wait_for_timeout(
                500
            )

            options = page.get_by_text(
                "4 نفر",
                exact=True
            )

            selected = False

            for i in range(
                await options.count()
            ):

                option = options.nth(i)

                try:

                    if await option.is_visible():

                        await option.click()

                        selected = True

                        print(
                            "Selected: 4 نفر"
                        )

                        break

                except Exception:
                    pass

            if not selected:

                print(
                    "WARNING: 4 نفر option "
                    "was not selected."
                )

            await page.wait_for_timeout(
                1000
            )

            # =================================================
            # مهم:
            # دیگر تاریخ‌ها را کلیک نمی‌کنیم.
            #
            # مستقیماً قیمت تقویم را می‌خوانیم.
            # =================================================

            print(
                "\n===== READING CALENDAR PRICES ====="
            )

            price_28 = await get_calendar_price(
                page,
                DATE_28
            )

            price_29 = await get_calendar_price(
                page,
                DATE_29
            )

            if price_28 is None:

                raise Exception(
                    "Could not find price for "
                    "28 Mordad."
                )

            if price_29 is None:

                raise Exception(
                    "Could not find price for "
                    "29 Mordad."
                )

            total = (
                price_28 +
                price_29
            )

            current = {
                "room_code": ROOM_CODE,
                "room_name": ROOM_NAME,
                "guests": GUESTS,
                "checkin": CHECKIN_DATE,
                "checkout": CHECKOUT_DATE,
                "price_28": price_28,
                "price_29": price_29,
                "total": total
            }

            # =================================================
            # REPORT
            # =================================================

            print(
                "\n========================================"
            )

            print(
                "===== JAJIGA PRICE REPORT ====="
            )

            print(
                f"اقامتگاه: {ROOM_NAME}"
            )

            print(
                f"کد: {ROOM_CODE}"
            )

            print(
                f"مهمان: {GUESTS} نفر"
            )

            print()

            print(
                f"28 مرداد: "
                f"{format_price(price_28)} تومان"
            )

            print(
                f"29 مرداد: "
                f"{format_price(price_29)} تومان"
            )

            print()

            print(
                f"مجموع دو شب: "
                f"{format_price(total)} تومان"
            )

            print(
                "========================================"
            )

            # =================================================
            # LOAD OLD PRICE
            # =================================================

            old = load_state()

            # =================================================
            # FIRST RUN
            # =================================================

            if old is None:

                print(
                    "\nNo previous price found."
                )

                print(
                    "Saving initial price..."
                )

                save_state(
                    price_28,
                    price_29,
                    total
                )

                print(
                    "Initial price saved."
                )

            else:

                old_total = old.get(
                    "total"
                )

                old_price_28 = old.get(
                    "price_28"
                )

                old_price_29 = old.get(
                    "price_29"
                )

                # =============================================
                # PRICE CHANGE?
                # =============================================

                changed = (
                    old_total != total
                    or
                    old_price_28 != price_28
                    or
                    old_price_29 != price_29
                )

                if not changed:

                    print(
                        "\nNo price change."
                    )

                else:

                    print(
                        "\n🔔 PRICE CHANGE DETECTED"
                    )

                    message = (
                        build_price_change_message(
                            old,
                            current
                        )
                    )

                    print(
                        "\n===== TELEGRAM MESSAGE ====="
                    )

                    print(
                        message
                    )

                    print(
                        "============================"
                    )

                    # =========================================
                    # SEND TELEGRAM
                    # =========================================

                    send_telegram(
                        message
                    )

                # =============================================
                # ALWAYS SAVE LATEST PRICE
                # =============================================

                save_state(
                    price_28,
                    price_29,
                    total
                )

                print(
                    "\nLatest price saved."
                )

            # =================================================
            # SCREENSHOT
            # =================================================

            try:

                await page.screenshot(
                    path="jajiga_calendar.png",
                    full_page=True
                )

                print(
                    "Screenshot saved: "
                    "jajiga_calendar.png"
                )

            except Exception as e:

                print(
                    "Screenshot warning:",
                    e
                )

    except Exception as e:

        print(
            "\n========================================"
        )

        print(
            "ERROR:"
        )

        print(
            str(e)
        )

        print(
            "========================================"
        )

        raise

    finally:

        if browser:

            try:

                await browser.close()

            except Exception:
                pass


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    asyncio.run(main())
