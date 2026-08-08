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

ROOM_ID = "3159346"
ROOM_NAME = "ویلا لب دریا در بندرانزلی - کپورچال"

GUESTS = 4

CHECKIN = "1405-05-28"
CHECKOUT = "1405-05-30"

DATE_28 = "1405-05-28"
DATE_29 = "1405-05-29"

DATE_28_LABEL = "28 مرداد"
DATE_29_LABEL = "29 مرداد"

HISTORY_FILE = Path("price_history.json")

# GitHub Secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# =========================================================
# PERSIAN NUMBER HELPERS
# =========================================================

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"


def normalize_digits(text):
    """Convert Persian/Arabic digits to English digits."""

    if text is None:
        return ""

    text = str(text)

    translation = {}

    for i, digit in enumerate(PERSIAN_DIGITS):
        translation[ord(digit)] = ENGLISH_DIGITS[i]

    for i, digit in enumerate(ARABIC_DIGITS):
        translation[ord(digit)] = ENGLISH_DIGITS[i]

    return text.translate(translation)


def parse_price(text):
    """
    Convert:
        5٬000٬000
        5,000,000
        5.000.000 تومان
    to:
        5000000
    """

    if text is None:
        return None

    text = normalize_digits(text)

    # Remove common Persian/Arabic separators and everything
    # except digits.
    digits = re.sub(r"[^\d]", "", text)

    if not digits:
        return None

    try:
        return int(digits)
    except ValueError:
        return None


def format_price(value):
    """Format number as 5٬000٬000 تومان."""

    if value is None:
        return "نامشخص"

    return f"{value:,}".replace(",", "٬") + " تومان"


def format_number(value):
    """Format number without تومان."""

    if value is None:
        return "نامشخص"

    return f"{value:,}".replace(",", "٬")


# =========================================================
# HISTORY
# =========================================================

def load_history():
    """Load previous successful price data."""

    if not HISTORY_FILE.exists():
        return None

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None

        return data

    except Exception as e:
        print(f"WARNING: Could not read history: {e}")
        return None


def save_history(data):
    """Save current price data."""

    try:
        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        print(f"History saved to {HISTORY_FILE}")

    except Exception as e:
        print(f"WARNING: Could not save history: {e}")


# =========================================================
# TELEGRAM
# =========================================================

def send_telegram_message(message):
    """Send notification to Telegram."""

    if not TELEGRAM_BOT_TOKEN:
        print("WARNING: TELEGRAM_BOT_TOKEN is not set.")
        return False

    if not CHAT_ID:
        print("WARNING: CHAT_ID is not set.")
        return False

    api_url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
    }

    try:

        response = requests.post(
            api_url,
            json=payload,
            timeout=30
        )

        print(
            "Telegram status:",
            response.status_code
        )

        if response.ok:
            print("Telegram message sent.")
            return True

        print(
            "Telegram error:",
            response.text
        )

        return False

    except Exception as e:

        print(
            "Telegram exception:",
            e
        )

        return False


# =========================================================
# PRICE EXTRACTION
# =========================================================

async def get_calendar_price(page, date):
    """
    Read price from:

    [data-test="calendar-day-YYYY-MM-DD"]

    Example:
        '28\n5٬000٬000'
    """

    selector = (
        f'[data-test="calendar-day-{date}"]'
    )

    elements = page.locator(selector)

    count = await elements.count()

    print(
        f"{date} elements: {count}"
    )

    if count == 0:
        print(
            f"WARNING: {date} not found."
        )
        return None

    for i in range(count):

        try:

            element = elements.nth(i)

            raw_text = await element.inner_text()

            raw_text = raw_text.strip()

            print(
                f"{date} raw text: "
                f"{raw_text!r}"
            )

            # Find numbers containing separators.
            matches = re.findall(
                r"[\d۰-۹٠-٩][\d۰-۹٠-٩٬,.\s]*",
                raw_text
            )

            # Prefer a number that is large enough to
            # reasonably be a room price.
            for match in matches:

                price = parse_price(match)

                if price is not None and price >= 100000:

                    print(
                        f"PRICE FOUND {date}: "
                        f"{format_number(price)}"
                    )

                    return price

        except Exception as e:

            print(
                f"WARNING reading {date}: {e}"
            )

    print(
        f"WARNING: PRICE NOT FOUND {date}"
    )

    return None


# =========================================================
# SELECT GUESTS
# =========================================================

async def select_guests(page):
    """Select 4 guests."""

    guest_input = page.locator(
        '[data-test="room-booking-guests"]'
    )

    count = await guest_input.count()

    print(
        "Guest input count:",
        count
    )

    if count == 0:
        raise RuntimeError(
            "Guest input not found."
        )

    # Use the first visible guest input.
    selected_input = None

    for i in range(count):

        try:

            candidate = guest_input.nth(i)

            if await candidate.is_visible():

                selected_input = candidate
                break

        except Exception:
            pass

    if selected_input is None:

        raise RuntimeError(
            "Visible guest input not found."
        )

    await selected_input.click()

    await page.wait_for_timeout(700)

    # Exact "4 نفر"
    options = page.get_by_text(
        "4 نفر",
        exact=True
    )

    option_count = await options.count()

    print(
        "4-person options found:",
        option_count
    )

    for i in range(option_count):

        try:

            option = options.nth(i)

            if await option.is_visible():

                await option.click()

                print(
                    "Selected: 4 نفر"
                )

                await page.wait_for_timeout(700)

                return True

        except Exception:
            pass

    raise RuntimeError(
        "Could not select 4 نفر."
    )


# =========================================================
# READ CURRENT PRICES
# =========================================================

async def read_current_prices(page):

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
        raise RuntimeError(
            "Price for 28 Mordad could not be found."
        )

    if price_29 is None:
        raise RuntimeError(
            "Price for 29 Mordad could not be found."
        )

    total = price_28 + price_29

    return {
        "room_id": ROOM_ID,
        "room_name": ROOM_NAME,
        "guests": GUESTS,
        "checkin": CHECKIN,
        "checkout": CHECKOUT,
        "price_28": price_28,
        "price_29": price_29,
        "total": total,
    }


# =========================================================
# REPORT
# =========================================================

def print_report(data):

    print()
    print("=" * 40)
    print("===== JAJIGA PRICE REPORT =====")
    print(
        f"اقامتگاه: {ROOM_NAME}"
    )
    print(
        f"کد: {ROOM_ID}"
    )
    print(
        f"مهمان: {GUESTS} نفر"
    )
    print()

    print(
        f"{DATE_28_LABEL}: "
        f"{format_price(data['price_28'])}"
    )

    print(
        f"{DATE_29_LABEL}: "
        f"{format_price(data['price_29'])}"
    )

    print()

    print(
        f"مجموع دو شب: "
        f"{format_price(data['total'])}"
    )

    print("=" * 40)


# =========================================================
# PRICE CHANGE
# =========================================================

def build_price_change_message(old, new):

    old_total = old.get("total")
    new_total = new.get("total")

    old_28 = old.get("price_28")
    new_28 = new.get("price_28")

    old_29 = old.get("price_29")
    new_29 = new.get("price_29")

    # -----------------------------------------------------
    # Safety:
    # Do NOT subtract None values.
    # -----------------------------------------------------

    if (
        old_total is None
        or new_total is None
    ):
        return None

    total_change = (
        new_total - old_total
    )

    # No total change
    if total_change == 0:

        return None

    if total_change < 0:

        change_title = "کاهش قیمت"

        change_amount = abs(
            total_change
        )

    else:

        change_title = "افزایش قیمت"

        change_amount = abs(
            total_change
        )

    lines = []

    lines.append(
        "🔔 تغییر قیمت جاجیگا"
    )

    lines.append(
        f"اقامتگاه: {ROOM_NAME}"
    )

    lines.append(
        "تاریخ: ۲۸ تا ۳۰ مرداد"
    )

    lines.append(
        f"مهمان: {GUESTS} نفر"
    )

    lines.append(
        f"قیمت قبلی: {format_price(old_total)}"
    )

    lines.append(
        f"قیمت جدید: {format_price(new_total)}"
    )

    lines.append(
        f"{change_title}: "
        f"{format_price(change_amount)}"
    )

    lines.append("")

    # -----------------------------------------------------
    # 28 Mordad
    # -----------------------------------------------------

    if (
        old_28 is not None
        and new_28 is not None
        and old_28 != new_28
    ):

        diff_28 = new_28 - old_28

        if diff_28 < 0:

            label_28 = "کاهش قیمت"

        else:

            label_28 = "افزایش قیمت"

        lines.append(
            f"قیمت قدیم 28 مرداد: "
            f"{format_price(old_28)}"
        )

        lines.append(
            f"قیمت جدید 28 مرداد: "
            f"{format_price(new_28)}"
        )

        lines.append(
            f"{label_28} 28 مرداد: "
            f"{format_price(abs(diff_28))}"
        )

        lines.append("")

    # -----------------------------------------------------
    # 29 Mordad
    # -----------------------------------------------------

    if (
        old_29 is not None
        and new_29 is not None
        and old_29 != new_29
    ):

        diff_29 = new_29 - old_29

        if diff_29 < 0:

            label_29 = "کاهش قیمت"

        else:

            label_29 = "افزایش قیمت"

        lines.append(
            f"قیمت قدیم 29 مرداد: "
            f"{format_price(old_29)}"
        )

        lines.append(
            f"قیمت جدید 29 مرداد: "
            f"{format_price(new_29)}"
        )

        lines.append(
            f"{label_29} 29 مرداد: "
            f"{format_price(abs(diff_29))}"
        )

    return "\n".join(lines)


# =========================================================
# MAIN
# =========================================================

async def main():

    print("=" * 40)
    print("===== JAJIGA PRICE MONITOR =====")
    print("=" * 40)

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        context = await browser.new_context(
            viewport={
                "width": 1440,
                "height": 1200,
            },
            locale="fa-IR",
        )

        page = await context.new_page()

        try:

            # =============================================
            # OPEN JAJIGA
            # =============================================

            print(
                "Opening Jajiga..."
            )

            await page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            await page.wait_for_timeout(
                5000
            )

            print(
                "Page loaded"
            )

            # =============================================
            # GUESTS
            # =============================================

            await select_guests(page)

            await page.wait_for_timeout(
                1000
            )

            # =============================================
            # READ PRICES DIRECTLY FROM CALENDAR
            # =============================================

            current = await read_current_prices(
                page
            )

            # =============================================
            # REPORT
            # =============================================

            print_report(
                current
            )

            # =============================================
            # LOAD PREVIOUS DATA
            # =============================================

            previous = load_history()

            # =============================================
            # FIRST RUN
            # =============================================

            if previous is None:

                print()
                print(
                    "No previous price history found."
                )

                print(
                    "Saving current prices as baseline."
                )

                save_history(
                    current
                )

                print(
                    "No Telegram notification "
                    "on first run."
                )

            else:

                print()
                print(
                    "===== PREVIOUS PRICE ====="
                )

                print(
                    f"28 مرداد: "
                    f"{format_price(previous.get('price_28'))}"
                )

                print(
                    f"29 مرداد: "
                    f"{format_price(previous.get('price_29'))}"
                )

                print(
                    f"مجموع: "
                    f"{format_price(previous.get('total'))}"
                )

                # =========================================
                # VALIDATE OLD DATA
                # =========================================

                required_keys = [
                    "price_28",
                    "price_29",
                    "total",
                ]

                history_valid = all(
                    previous.get(key) is not None
                    for key in required_keys
                )

                if not history_valid:

                    print()
                    print(
                        "WARNING: Previous history "
                        "is incomplete."
                    )

                    print(
                        "Replacing incomplete history "
                        "with current prices."
                    )

                    save_history(
                        current
                    )

                    print(
                        "No notification sent because "
                        "there is no valid baseline."
                    )

                else:

                    # =====================================
                    # COMPARE
                    # =====================================

                    changed = (
                        previous["price_28"]
                        != current["price_28"]
                        or
                        previous["price_29"]
                        != current["price_29"]
                        or
                        previous["total"]
                        != current["total"]
                    )

                    if not changed:

                        print()
                        print(
                            "No price change detected."
                        )

                    else:

                        print()
                        print(
                            "🔔 PRICE CHANGE DETECTED"
                        )

                        message = (
                            build_price_change_message(
                                previous,
                                current
                            )
                        )

                        if message:

                            print()
                            print(
                                "===== TELEGRAM MESSAGE ====="
                            )

                            print(
                                message
                            )

                            print(
                                "============================"
                            )

                            send_telegram_message(
                                message
                            )

                        else:

                            print(
                                "Price changed but "
                                "notification could not "
                                "be built."
                            )

                    # =====================================
                    # ALWAYS UPDATE BASELINE
                    # =====================================

                    save_history(
                        current
                    )

        except Exception as e:

            print()
            print("=" * 40)
            print("ERROR")
            print("=" * 40)

            print(
                repr(e)
            )

            # Try to save a screenshot for debugging.
            try:

                await page.screenshot(
                    path="jajiga_error.png",
                    full_page=True,
                )

                print(
                    "Debug screenshot saved: "
                    "jajiga_error.png"
                )

            except Exception:
                pass

            raise

        finally:

            await browser.close()

    print()
    print(
        "===== FINISHED ====="
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
