import asyncio
import json
import os
import re
from pathlib import Path
import requests
from playwright.async_api import async_playwright

URL = 'https://www.jajiga.com/room/3159346'
ROOM_CODE = '3159346'
ROOM_NAME = 'ویلا لب دریا در بندرانزلی - کپورچال'
GUESTS = 4
CHECKIN_DATE = '1405-05-28'
CHECKOUT_DATE = '1405-05-30'
DATE_28 = '1405-05-28'
DATE_29 = '1405-05-29'
STATE_FILE = Path('price_state.json')
SCREENSHOT_FILE = 'jajiga_calendar.png'
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()

def normalize_digits(text):
    if not text: return ''
    return text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789'))

def parse_price(text):
    if not text: return None
    text = normalize_digits(text).replace('٬','').replace(',','').replace('،','').replace('تومان','').strip()
    m = re.search(r'\d{5,}', text)
    return int(m.group()) if m else None

def format_price(price):
    return 'نامشخص' if price is None else f'{int(price):,}'.replace(',', '٬')

def format_change(change):
    return format_price(abs(int(change)))

def load_state():
    if not STATE_FILE.exists(): return None
    try:
        with STATE_FILE.open(encoding='utf-8') as f: data=json.load(f)
        if any(data.get(k) is None for k in ('price_28','price_29','total')):
            print('WARNING: Existing price state is incomplete. Resetting baseline.')
            return None
        return data
    except Exception as e:
        print('WARNING: Could not read state file:', e); return None

def save_state(price_28, price_29, total):
    data={'room_code':ROOM_CODE,'room_name':ROOM_NAME,'guests':GUESTS,'checkin':CHECKIN_DATE,'checkout':CHECKOUT_DATE,'price_28':int(price_28),'price_29':int(price_29),'total':int(total)}
    tmp=STATE_FILE.with_suffix('.tmp')
    with tmp.open('w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    tmp.replace(STATE_FILE)

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print('WARNING: Telegram credentials are not configured.'); return False
    try:
        r=requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',json={'chat_id':TELEGRAM_CHAT_ID,'text':message},timeout=30)
        r.raise_for_status(); result=r.json()
        if not result.get('ok'): print('Telegram error:',result); return False
        print('Telegram message sent successfully.'); return True
    except Exception as e:
        print('Telegram send error:',e); return False

def build_price_change_message(old,new):
    vals=[old.get('total'),old.get('price_28'),old.get('price_29'),new.get('total'),new.get('price_28'),new.get('price_29')]
    if any(v is None for v in vals):
        return '\n'.join(['🔔 تغییر قیمت جاجیگا','',f'اقامتگاه: {ROOM_NAME}','وضعیت: قیمت جدید دریافت شد، اما سابقه قبلی کامل نبود.','',f"قیمت جدید ۲۸ مرداد: {format_price(new.get('price_28'))} تومان",f"قیمت جدید ۲۹ مرداد: {format_price(new.get('price_29'))} تومان",f"مجموع جدید: {format_price(new.get('total'))} تومان"])
    total_change=new['total']-old['total']
    direction='کاهش قیمت' if total_change<0 else 'افزایش قیمت'
    lines=['🔔 تغییر قیمت جاجیگا','',f'اقامتگاه: {ROOM_NAME}','تاریخ: ۲۸ تا ۳۰ مرداد',f'مهمان: {GUESTS} نفر','',f"قیمت قبلی: {format_price(old['total'])} تومان",f"قیمت جدید: {format_price(new['total'])} تومان"]
    if total_change: lines.append(f'{direction}: {format_change(total_change)} تومان')
    lines += ['', '━━━━━━━━━━━━━━', '', 'قیمت‌های شبانه:', '',f"قیمت قدیم ۲۸ مرداد: {format_price(old['price_28'])} تومان",f"قیمت جدید ۲۸ مرداد: {format_price(new['price_28'])} تومان"]
    c28=new['price_28']-old['price_28']
    if c28: lines.append(f"{'کاهش' if c28<0 else 'افزایش'} قیمت ۲۸ مرداد: {format_change(c28)} تومان")
    lines += ['',f"قیمت قدیم ۲۹ مرداد: {format_price(old['price_29'])} تومان",f"قیمت جدید ۲۹ مرداد: {format_price(new['price_29'])} تومان"]
    c29=new['price_29']-old['price_29']
    if c29: lines.append(f"{'کاهش' if c29<0 else 'افزایش'} قیمت ۲۹ مرداد: {format_change(c29)} تومان")
    return '\n'.join(lines)

async def get_calendar_price(page,date):
    locator=page.locator(f'[data-test="calendar-day-{date}"]')
    count=await locator.count(); print(f'{date} elements: {count}')
    if not count: return None
    expected=str(int(date[-2:]))
    for i in range(count):
        try:
            text=(await locator.nth(i).inner_text()).strip(); print(f'{date} raw text: {text!r}')
            for line in [x.strip() for x in text.splitlines() if x.strip()]:
                if normalize_digits(line)==expected: continue
                price=parse_price(line)
                if price is not None and price>=100000:
                    print(f'PRICE FOUND {date}: {format_price(price)}'); return price
        except Exception as e: print(f'WARNING reading {date}:',e)
    return None

async def select_guests(page):
    guest=page.locator('[data-test="room-booking-guests"]')
    count=await guest.count(); print('Guest input count:',count)
    if not count: raise RuntimeError('Guest input not found.')
    try: current=await guest.first.input_value()
    except Exception: current=''
    if current.strip()=='4 نفر': print('Selected: 4 نفر'); return
    await guest.first.click(); await page.wait_for_timeout(500)
    options=page.get_by_text('4 نفر',exact=True); print('4-person options found:',await options.count())
    for i in range(await options.count()):
        try:
            if await options.nth(i).is_visible():
                await options.nth(i).click(); print('Selected: 4 نفر'); await page.wait_for_timeout(1000); return
        except Exception: pass
    raise RuntimeError('Could not select 4 نفر.')

async def main():
    print('========================================'); print('===== JAJIGA PRICE MONITOR ====='); print('========================================')
    browser=None
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True)
            page=await browser.new_page(viewport={'width':1440,'height':1200},locale='fa-IR')
            print('Opening Jajiga...')
            await page.goto(URL,wait_until='domcontentloaded',timeout=60000); await page.wait_for_timeout(5000); print('Page loaded')
            await select_guests(page)
            print('\n===== READING CALENDAR PRICES =====')
            price_28=await get_calendar_price(page,DATE_28); price_29=await get_calendar_price(page,DATE_29)
            if price_28 is None: raise RuntimeError('Could not find price for 28 Mordad.')
            if price_29 is None: raise RuntimeError('Could not find price for 29 Mordad.')
            total=price_28+price_29
            current={'room_code':ROOM_CODE,'room_name':ROOM_NAME,'guests':GUESTS,'checkin':CHECKIN_DATE,'checkout':CHECKOUT_DATE,'price_28':price_28,'price_29':price_29,'total':total}
            print('\n========================================'); print('===== JAJIGA PRICE REPORT ====='); print(f'اقامتگاه: {ROOM_NAME}'); print(f'کد: {ROOM_CODE}'); print(f'مهمان: {GUESTS} نفر'); print(); print(f'28 مرداد: {format_price(price_28)} تومان'); print(f'29 مرداد: {format_price(price_29)} تومان'); print(); print(f'مجموع دو شب: {format_price(total)} تومان'); print('========================================')
            old=load_state()
            if old is None:
                print('\nNo previous price history found.'); print('Saving current prices as baseline.'); save_state(price_28,price_29,total); print('History saved to price_state.json'); print('No Telegram notification on first run.')
            else:
                oldvals=(old.get('price_28'),old.get('price_29'),old.get('total'))
                if any(v is None for v in oldvals):
                    print('\nPrevious history is incomplete. Replacing it with current baseline.'); save_state(price_28,price_29,total)
                elif old['price_28']!=price_28 or old['price_29']!=price_29 or old['total']!=total:
                    print('\n🔔 PRICE CHANGE DETECTED'); message=build_price_change_message(old,current); print('\n===== TELEGRAM MESSAGE ====='); print(message); print('============================'); send_telegram(message); save_state(price_28,price_29,total); print('\nLatest price saved.')
                else:
                    print('\nNo price change.'); save_state(price_28,price_29,total)
            try:
                await page.screenshot(path=SCREENSHOT_FILE,full_page=True); print(f'Screenshot saved: {SCREENSHOT_FILE}')
            except Exception as e: print('Screenshot warning:',e)
    except Exception as e:
        print('\n========================================'); print('ERROR:'); print(str(e)); print('========================================'); raise
    finally:
        if browser:
            try: await browser.close()
            except Exception: pass

if __name__=='__main__': asyncio.run(main())
