import asyncio
import os
import re
import random
import string
from urllib.parse import urlparse, parse_qs
from telethon import TelegramClient, events
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import expect
import io
import base64
import json
from telethon.tl.types import DocumentAttributeFilename
import tempfile
import shutil
from faker import Faker

#===============================
API_ID = '30687411'
API_HASH = '8fe205c97b03657f280f62832296680f'
BOT_TOKEN = '7848279718:AAHuK4uSPQQfRmwKxi-YbSDh_NGXaVxIjh0'

client = TelegramClient('AM2_D3', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

fake = Faker()

# ==========================================
# إعدادات البروكسي الدوار (711Proxy - Aruba)
# ==========================================
PROXY_USER_BASE = "USER608261-zone-custom-region-AW-st-Aruba"
PROXY_PASS = "1279bb"
PROXY_HOST = "global.rotgb.711proxy.com"
PROXY_PORT = "10000"

def generate_random_st(length: int = 10) -> str:
    """توليد session token عشوائي لجعل الـ IP يتغير في كل مرة"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))

def get_rotating_proxy() -> dict:
    """
    إنشاء بروكسي جديد بجلسة عشوائية => IP جديد في كل مرة
    """
    st = generate_random_st()
    username = f"{PROXY_USER_BASE}-{st}"
    proxy_url = f"http://{username}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    return {
        "server": proxy_url,
        "username": username,
        "password": PROXY_PASS,
    }

def get_playwright_proxy() -> dict:
    """صيغة البروكسي الخاصة بـ Playwright"""
    st = generate_random_st()
    username = f"{PROXY_USER_BASE}-{st}"
    return {
        "server": f"http://{PROXY_HOST}:{PROXY_PORT}",
        "username": username,
        "password": PROXY_PASS,
    }


# ==========================================
# المتصفح الوهمي (User-Agent + viewport عشوائي)
# ==========================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1600, "height": 900},
    {"width": 1366, "height": 768},
]

LOCALES = ["en-US", "en-GB", "fr-FR", "ar-DZ", "ar-MA"]

TIMEZONES = ["Africa/Algiers", "Africa/Casablanca", "Europe/Paris", "Europe/London", "Atlantic/Canary"]

def get_random_ua() -> str:
    return random.choice(USER_AGENTS)

def get_random_viewport() -> dict:
    return random.choice(VIEWPORTS)

def get_random_locale() -> str:
    return random.choice(LOCALES)

def get_random_timezone() -> str:
    return random.choice(TIMEZONES)

# سكريبت إخفاء بصمات الأتمتة داخل الصفحة
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = { runtime: {} };
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);
"""


# ==========================================
VLESS_TEMPLATE = (
    "vless://aaaa1111-bbbb-4ccc-8ddd-eeeeffff0000@google.com:443"
    "?path=%2Fby_moon&security=tls&encryption=none"
    "&host={domain}&type=ws&sni={domain}#moon_algerie-moon"
)


JSON_TEMPLATE = r'''{
  "dns": {
    "fallbackStrategy": "disabledIfAnyMatch",
    "hosts": {},
    "servers": [
      {
        "address": "tcp://8.8.8.8",
        "fakedns": [
          {
            "ipPool": "198.18.0.0/15",
            "poolSize": 65535
          }
        ],
        "queryStrategy": "UseIPv4"
      }
    ]
  },
  "inbounds": [
    {
      "listen": "0.0.0.0",
      "port": "1080",
      "protocol": "dokodemo-door",
      "settings": {
        "network": "tcp,udp",
        "followRedirect": true
      },
      "tag": "tun-inbound"
    },
    {
      "listen": "127.0.0.1",
      "port": "10808",
      "protocol": "socks",
      "settings": {
        "auth": "noauth",
        "udp": true
      },
      "tag": "socks-inbound"
    }
  ],
  "log": {
    "loglevel": "warning"
  },
  "outbounds": [
    {
      "mux": {
        "enabled": false
      },
      "protocol": "vless",
      "proxySettings": {
        "tag": "AhMed",
        "transportLayer": true
      },
      "settings": {
        "vnext": [
          {
            "address": "yt3.ggpht.com",
            "port": 443,
            "users": [
              {
                "encryption": "none",
                "flow": "",
                "id": "aaaa1111-bbbb-4ccc-8ddd-eeeeffff0000",
                "level": 8
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "tlsSettings": {
          "allowInsecure": true,
          "serverName": "yt3.ggpht.com"
        },
        "wsSettings": {
          "headers": {
            "Host": "__DOMAIN__"
          },
          "path": "/by_moon"
        }
      },
      "tag": "VLESS"
    },
    {
      "domainStrategy": "AsIs",
      "protocol": "http",
      "settings": {
        "servers": [
          {
            "address": "57.144.120.4",
            "port": 8080
          }
        ],
        "headers": {
          "Host": "yt3.ggpht.com:443",
          "Proxy-Connection": "keep-alive",
          "User-Agent": "FBAV/0.0",
          "X-iorg-bsid": "moon_algerie-moon"
        }
      },
      "tag": "moon_algerie-moon"
    },
    {
      "protocol": "freedom",
      "tag": "direct"
    },
    {
      "protocol": "blackhole",
      "tag": "block"
    }
  ],
  "policy": {
    "levels": {
      "8": {
        "connIdle": 300,
        "downlinkOnly": 1,
        "handshake": 4,
        "uplinkOnly": 1
      }
    }
  },
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "outboundTag": "direct",
        "protocol": [
          "dns"
        ],
        "type": "field"
      },
      {
        "inboundTag": [
          "tun-inbound",
          "socks-inbound"
        ],
        "outboundTag": "VLESS",
        "type": "field"
      }
    ]
  }
}'''


DARKTUNNEL_BASE_URI = "darktunnel://eyJ0eXBlIjoiVkxFU1MiLCJuYW1lIjoi2YXYrNin2YbZiiDYp9iz2YrYpyDZiCDYp9ir2YrYsSAiLCJ2bGVzc1R1bm5lbENvbmZpZyI6eyJ2MnJheUNvbmZpZyI6eyJob3N0IjoiYWx0MTMueXQzLmdncGh0LmNvbSIsInBvcnQiOjQ0MywidXVpZCI6ImFhYWExMTExLWJiYmItNGNjYy04ZGRkLWVlZWVmZmZmMDAwMCIsInNlcnZlck5hbWVJbmRpY2F0aW9uIjoiYWx0MTMueXQzLmdncGh0LmNvbSIsIndzUGF0aCI6Ii9ieV9tb29uIiwid3NIZWFkZXJIb3N0IjoiYWhtZWQtdmlwMS00MTQwMDg2MTIxMjMuZXVyb3BlLXdlc3QxLnJ1bi5hcHAifSwiaW5qZWN0Q29uZmlnIjp7ImVuYWJsZWQiOnRydWUsIm1vZGUiOiJQUk9YWSIsInByb3h5SG9zdCI6IjE1Ny4yNDAuOS4zOSIsInBheWxvYWQiOiJDT05ORUNUIFtob3N0XTpbcG9ydF0gSFRUUC8xLjFbY3JsZl14LWNvbm5lY3RlZC10bzogMzQuMTQzLjcyLjJbY3JsZl1wcm94eS1jb25uZWN0aW9uOiBrZWVwLWFsaXZlW2NybGZdY29ubmVjdGlvbjoga2VlcC1hbGl2ZVtjcmxmXXVzZXItYWdlbnQ6IEZCQVYvMC4wIFtjcmxmXXgtaW9yZy1ic2lkOiBtb29uX2FsZ2VyaWUtbW9vbltjcmxmXVtjcmxmXSJ9fX0"


# ==========================================
# ==========================================

async def handle_error(page, chat_id, step_name, error_msg):
    print(f"Error at {step_name}: {error_msg}")
    screenshot_path = f"error_{step_name}.png"
    try:
        await page.screenshot(path=screenshot_path, full_page=True)
        safe_error_msg = str(error_msg)[:900] + "\n... (تم تقصير الرسالة)" if len(str(error_msg)) > 800 else str(error_msg)
        
        await client.send_file(
            chat_id, 
            file=screenshot_path, 
            caption=f"❌ حدث خطأ في مرحلة:\n**{step_name}**\n\nتفاصيل الخطأ:\n`{safe_error_msg}`"
        )
        os.remove(screenshot_path)
    except Exception as e:
        await client.send_message(chat_id, f"❌ حدث خطأ قاتل وما كدرت اخذ سكرين: {str(e)}")


# ==========================================
def extract_domain_from_service_url(service_url: str) -> str:
    s = (service_url or "").strip()
    if s.startswith("http://") or s.startswith("https://"):
        return urlparse(s).netloc.strip()
    return s.replace("http://", "").replace("https://", "").split("/")[0].strip()

def _b64_pad(s: str) -> str:
    return s + ("=" * ((4 - (len(s) % 4)) % 4)) if s else s

def darktunnel_decode(uri: str) -> dict:
    b64 = _b64_pad(uri.split("darktunnel://", 1)[1].strip())
    return json.loads(base64.b64decode(b64.encode("utf-8")).decode("utf-8"))

def darktunnel_encode(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "darktunnel://" + base64.b64encode(raw).decode("utf-8")

def build_darktunnel_uri_with_host(new_host: str) -> str:
    data = darktunnel_decode(DARKTUNNEL_BASE_URI)
    
    stack = [data]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            if "wsHeaderHost" in cur:
                cur["wsHeaderHost"] = new_host
            stack.extend(v for v in cur.values() if isinstance(v, (dict, list)))
        elif isinstance(cur, list):
            stack.extend(v for v in cur if isinstance(v, (dict, list)))
            
    return darktunnel_encode(data)

async def generate_and_send_dark_file(chat_id: int, domain: str):
    new_uri = build_darktunnel_uri_with_host(domain)
    safe_domain = re.sub(r"[^a-z0-9\.\-]+", "_", domain.lower()).strip("_")
    tg_fname = f"moon_algerie-moon - {safe_domain}.dark"
    
    bio = io.BytesIO(new_uri.encode("utf-8"))
    bio.name = tg_fname 
    await client.send_file(
        chat_id,
        bio,
        force_document=True,
        attributes=[DocumentAttributeFilename(tg_fname)],
        caption=f"✅ ملف DarkTunnel جاهز:\n`{domain}`"
    )


# ==========================================


def extract_project_id(url):
    match = re.search(r'(qwiklabs-gcp-[\w-]+)', url)
    if match:
        return match.group(1)
    return None

# ==========================================
# ==========================================

async def step1_welcome_screen(page):
    await page.wait_for_load_state("networkidle")
    
    await page.wait_for_timeout(2000)    
    await page.keyboard.press("Enter")
    
    try:
        button = page.locator("text='I understand'")
        if await button.is_visible(timeout=3000):
            await button.click()
    except:
        pass
    await page.wait_for_load_state("networkidle")

# ==========================================
async def step2_tos_and_country(page):
    agree_btn = page.get_by_role("button", name="Agree and continue")
    
    try:
        await agree_btn.wait_for(state="visible", timeout=10000)
        
        checkboxes = page.get_by_role("checkbox")
        await checkboxes.nth(0).click()
        await asyncio.sleep(1)
        await checkboxes.nth(1).click()
        
        await agree_btn.click()
        await page.wait_for_load_state("domcontentloaded")
        
    except Exception:
        print("رسالة الشروط لم تظهر، تم التخطي تلقائياً.")
        pass

# ==========================================

async def step3_enable_api(page, project_id, authuser):
    api_url = f"https://console.cloud.google.com/apis/library/run.googleapis.com?project={project_id}&authuser={authuser}"
    await page.goto(api_url, wait_until="domcontentloaded")
    
    enable_btn = page.get_by_role("button", name="Enable")
    manage_btn = page.get_by_role("button", name="Manage")
    disable_btn = page.get_by_text("Disable API") 
    
    try:
        await expect(enable_btn.or_(manage_btn)).to_be_visible(timeout=15000)
        if await enable_btn.is_visible():
            await enable_btn.click()
            await expect(manage_btn.or_(disable_btn)).to_be_visible(timeout=60000)
        elif await manage_btn.is_visible():
            pass 
    except Exception as e:
         raise Exception(f"عطل في إيجاد زر تفعيل الـ API: {str(e)}")

# ==========================================

async def step4_create_cloud_run(page, project_id, authuser):
    run_url = f"https://console.cloud.google.com/run/create?project={project_id}&authuser={authuser}"
    await page.goto(run_url, wait_until="domcontentloaded")
    
    await page.wait_for_timeout(5000)
    
    try:
        label = page.get_by_text("Container Image URL").first
        await label.click()
        await page.wait_for_timeout(500)
        
        await page.keyboard.type("docker.io/ajndjd2/ahmed-vip1", delay=50)
        
    except Exception as e:
        raise Exception(f"فشل في الضغط وكتابة الرابط: {str(e)}")
    
    await page.wait_for_timeout(3000)
    
    try:
        await page.get_by_role("radio", name="Allow public access").click()
        await page.get_by_role("radio", name="Instance-based").click()
        
        try:
            await page.get_by_role("button", name="Hide").click(timeout=2000)
        except:
            pass
            
        await page.keyboard.press("End")
        await page.wait_for_timeout(1000)
        
        create_btn = page.get_by_role("button", name="Create")
        await create_btn.click(force=True)
        
    except Exception as e:
        raise Exception(f"فشل في اختيار الإعدادات أو ضغط Create: {str(e)}")


# ==========================================
async def step5_get_deployed_url(page):
    link_locator = page.locator('a[href*="run.app"]')
    await link_locator.wait_for(state="visible", timeout=120000) 
    
    final_url = await link_locator.get_attribute("href")
    return final_url

# ==========================================

async def process_sso_link(chat_id, sso_url):
    project_id = extract_project_id(sso_url)
    if not project_id:
        await client.send_message(chat_id, "❌ Project ID في الرابط.")
        return

    await client.send_message(chat_id, "⏳ 𝙡𝙚𝙩 𝙢𝙚 𝙨𝙚𝙚 𝙬𝙝𝙖𝙩 𝙄 𝙘𝙖𝙣 𝙙𝙤...")

    # 🎭 توليد بصمة عشوائية للمتصفح الوهمي
    ua = get_random_ua()
    viewport = get_random_viewport()
    locale = get_random_locale()
    timezone = get_random_timezone()
    playwright_proxy = get_playwright_proxy()

    print(f"[BROWSER] UA={ua}")
    print(f"[PROXY] user={playwright_proxy['username']}")

    temp_dir = tempfile.mkdtemp()
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                channel='chrome',
                headless=False,
                proxy=playwright_proxy,   # 🔥 البروكسي الدوار
                user_agent=ua,             # 🔥 UA عشوائي
                viewport=viewport,         # 🔥 Viewport عشوائي
                locale=locale,
                timezone_id=timezone,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    f'--window-size={viewport["width"]},{viewport["height"]}',
                    '--disable-features=IsolateOrigins,site-per-process',
                ],
                ignore_default_args=["--enable-automation"],
            )
            
            page = context.pages[0]

            # 🛡️ حقن سكريبت إخفاء الأتمتة
            await page.add_init_script(STEALTH_SCRIPT)
            
            await page.goto(sso_url, wait_until="domcontentloaded", timeout=60000)
            
            
            await client.send_message(chat_id, "🔄 𝙎𝙩𝙚𝙥 𝙤𝙣𝙚...")
            await step1_welcome_screen(page)
            
            await client.send_message(chat_id, "⏳ 𝙩𝙖𝙠𝙞𝙣𝙜 𝙖 𝙘𝙞𝙜𝙖𝙧𝙚𝙩𝙩𝙚 𝙛𝙞𝙧𝙨𝙩...")
            await page.wait_for_url("**/home/dashboard**", timeout=45000)
            
            current_qs = parse_qs(urlparse(page.url).query)
            authuser = current_qs.get('authuser', ['1'])[0]
            
            await client.send_message(chat_id, f"🔄 𝙉𝙤𝙬 𝙨𝙩𝙚𝙥 𝙩𝙬𝙤...")
            await step2_tos_and_country(page)
            
            await client.send_message(chat_id, "🔄 𝙎𝙩𝙚𝙥 𝙩𝙝𝙧𝙚𝙚 𝙖𝙨 𝙛𝙖𝙨𝙩 𝙖𝙨 𝙄 𝙘𝙖𝙣 𝙗𝙧𝙤 ...")
            await step3_enable_api(page, project_id, authuser)
            
            await client.send_message(chat_id, "🔄 𝙣𝙤𝙬 𝙩𝙝𝙚 𝙧𝙚𝙖𝙡 𝙟𝙤𝙗: 𝙎𝙩𝙚𝙥 𝙛𝙤𝙪𝙧...")
            await step4_create_cloud_run(page, project_id, authuser)
            
            await client.send_message(chat_id, "⏳ 𝙬𝙖𝙞𝙩, 𝙟𝙪𝙨𝙩 𝙤𝙣𝙚 𝙘𝙞𝙜𝙖𝙧𝙚𝙩𝙩𝙚...")
            final_url = await step5_get_deployed_url(page)        
            domain = extract_domain_from_service_url(final_url)
            
            await client.send_message(chat_id, f"✅ **𝙃𝙚𝙧𝙚 𝙮𝙤𝙪 𝙜𝙤 𝙗𝙧𝙤**\n\n 𝙙𝙤𝙢𝙖𝙞𝙣 :\n {domain}")
            
            vless_result = VLESS_TEMPLATE.format(domain=domain)
            await client.send_message(
                chat_id, 
                f"🔗 <pre><code class=\"language-java\">{vless_result}</code></pre>", 
                parse_mode='html'
            )
            
            json_result = JSON_TEMPLATE.replace("__DOMAIN__", domain)
            await client.send_message(
                chat_id, 
                f"📄<pre><code class=\"language-json\">{json_result}</code></pre>", 
                parse_mode='html'
            )
            
            await generate_and_send_dark_file(chat_id, domain)
            
        except PlaywrightTimeoutError as e:
            await handle_error(page, chat_id, "انتهى وقت الانتظار (Timeout)", str(e))
        except Exception as e:
            await handle_error(page, chat_id, "خطأ عام", str(e))
        finally:
            if 'context' in locals():
                await context.close()
            shutil.rmtree(temp_dir, ignore_errors=True)


# ==========================================

@client.on(events.NewMessage(pattern=r"^/start$"))
async def start(event):
    welcome_msg = (
        "**مرحبا في بوت انشاء كونفيجات تلقائية**\n\n"
        "⏳ **الوقت:** 4 ساعات و 30 دقيقة (4:30 hours)\n"
        "🔗 **الرابط:**\n"
        "https://www.cloudskillsboost.google/focuses/20774?parent=catalog\n\n"
        "⏳ **الوقت:** 3 ساعات (3:00 hours)\n"
        "🔗 **الرابط:**\n"
        "https://www.skills.google/focuses/82384?parent=catalog\n\n"

        "@moonalgerie"
    )
    await event.reply(welcome_msg)


# ==========================================

@client.on(events.NewMessage(pattern=r'https://www\.skills\.google/google_sso.*'))
async def handler(event):
    sso_url = event.text
    asyncio.create_task(process_sso_link(event.chat_id, sso_url))

print("𝙘𝙤𝙣𝙣𝙚𝙘𝙩𝙚𝙙...")
client.run_until_disconnected()
