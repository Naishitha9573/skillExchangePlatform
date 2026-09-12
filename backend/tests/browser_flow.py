"""Run a real two-browser smoke test with disposable data and synthetic media.

Requires playwright and a locally installed Chrome. Starts/stops its own servers;
never reads or changes the development database. Screenshots go to .artifacts.
"""
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / '.artifacts' / 'browser'
ARTIFACTS.mkdir(parents=True, exist_ok=True)
API = 'http://127.0.0.1:8011/api/v1'
WEB = 'http://127.0.0.1:5178'
database = ARTIFACTS / f'browser-{secrets.token_hex(6)}.db'
environment = {**os.environ, 'DATABASE_URL': f'sqlite:///{database.as_posix()}', 'SECRET_KEY': secrets.token_urlsafe(48),
               'CORS_ORIGINS': WEB, 'VITE_API_URL': API, 'GOOGLE_CLIENT_ID': '', 'GOOGLE_CLIENT_SECRET': '',
               'GEMINI_API_KEY': '', 'STUN_URLS': '', 'TURN_URLS': '', 'TURN_SECRET': ''}
processes = []
logs = []


def start(command, cwd, name):
    log = (ARTIFACTS / f'{name}.log').open('w', encoding='utf-8')
    logs.append(log)
    process = subprocess.Popen(command, cwd=cwd, env=environment, stdout=log, stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    processes.append(process)


def wait_for(url):
    for _ in range(100):
        try:
            if httpx.get(url, timeout=1).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(.2)
    raise RuntimeError(f'Server did not become available: {url}')


def request(method, path, token=None, data=None):
    response = httpx.request(method, API + path, headers={'Authorization': f'Bearer {token}'} if token else {}, json=data)
    response.raise_for_status()
    return response.json()


def no_overflow(page):
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'), page.url


def screenshot(page, name):
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path=str(ARTIFACTS / name), full_page=True, animations='disabled')


try:
    start([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8011', '--ws-max-size', '65536'], ROOT / 'backend', 'api')
    start(['node', str(ROOT / 'frontend/node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', '5178', '--strictPort'], ROOT / 'frontend', 'web')
    wait_for(API.replace('/api/v1', '/health')); wait_for(WEB)
    password = 'BrowserTest123'
    accounts = [request('POST', '/auth/register', data={'email': f"{name.lower().replace(' ', '')}@example.com", 'full_name': name, 'password': password}) for name in ('Alex Morgan', 'Jordan Rivera', 'Outside Member')]
except Exception as error:
    # Fail loudly with validation details; the test never substitutes production data.
    print(error.response.text if isinstance(error, httpx.HTTPStatusError) else str(error))
    for process in reversed(processes):
        process.terminate(); process.wait(timeout=10)
    for log in logs:
        log.close()
    raise

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True, args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'])
        contexts = [browser.new_context(viewport={'width':1440,'height':1050},permissions=['camera','microphone'],timezone_id='Asia/Kolkata') for _ in range(3)]
        for context in contexts:
            context.add_init_script("""window.testSockets=[];const NativeWebSocket=window.WebSocket;window.WebSocket=class extends NativeWebSocket{constructor(...args){super(...args);window.testSockets.push(this);}};""")
        errors = []
        pages = [context.new_page() for context in contexts]
        for page in pages:
            page.on('pageerror', lambda error: errors.append(str(error)))
        alex, jordan, outsider = pages
        for page, account in zip(pages, accounts):
            page.goto(WEB + '/login')
            page.get_by_label('Email address').fill(account['user']['email'])
            page.get_by_label('Password', exact=True).fill(password)
            page.get_by_role('button', name='Sign in', exact=True).click()
            page.wait_for_url('**/dashboard')

        alex.goto(WEB + '/add-skill')
        alex.get_by_label('Skill title').fill('React mentoring')
        alex.get_by_label('Description').fill('Build a practical React component with me.')
        alex.get_by_role('button',name='Publish skill').click()
        alex.wait_for_url('**/dashboard')
        python_skill = request('POST','/skills',accounts[1]['access_token'],{'title':'Python fundamentals','type':'Offering','category':'Technology','description':'Build your first practical Python program.'})
        alex.goto(WEB + f"/skill/{python_skill['id']}")
        alex.get_by_label('Your offered skill').select_option(label='React mentoring')
        alex.get_by_label('A friendly introduction').fill('Let’s learn together!')
        alex.get_by_role('button',name='Send swap request').click()
        expect(alex.get_by_role('button',name='Request sent')).to_be_visible()
        jordan.goto(WEB + '/swaps')
        jordan.get_by_role('button',name='Accept',exact=True).click()
        expect(jordan.locator('.status.accepted')).to_be_visible()
        swap = request('GET','/swaps',accounts[0]['access_token'])[0]
        alex.goto(WEB + f"/messages/{accounts[1]['user']['id']}")
        expect(alex.get_by_text('Live connection',exact=True)).to_be_visible()
        alex.get_by_label('Your message').fill('Hello Jordan, ready to learn?')
        alex.get_by_role('button',name='Send message',exact=True).click()
        expect(alex.locator('.message-bubble p',has_text='Hello Jordan, ready to learn?')).to_be_visible()
        expect(jordan.locator('.navlinks .nav-unread')).to_have_text('1')
        jordan.goto(WEB + f"/messages/{accounts[0]['user']['id']}")
        jordan.bring_to_front()
        expect(jordan.locator('.message-bubble p',has_text='Hello Jordan, ready to learn?')).to_be_visible()
        jordan.get_by_label('Your message').fill('Absolutely. Let’s book a session.')
        jordan.get_by_role('button',name='Send message',exact=True).click()
        expect(alex.locator('.message-bubble p',has_text='Absolutely. Let’s book a session.')).to_be_visible()
        expect(alex.locator('[aria-label="Read"]')).to_be_visible()
        # Force a dropped connection and check durable catch-up after reconnect.
        contexts[0].set_offline(True)
        alex.evaluate('window.testSockets.at(-1).close(4000)')
        expect(alex.locator('.connection-pill')).to_contain_text('Reconnecting')
        jordan.get_by_label('Your message').fill('Saved while you were away.')
        jordan.get_by_role('button',name='Send message',exact=True).click()
        expect(jordan.locator('.message-bubble p',has_text='Saved while you were away.')).to_be_visible()
        contexts[0].set_offline(False)
        expect(alex.locator('.connection-pill')).to_contain_text('Live connection',timeout=15000)
        expect(alex.locator('.message-bubble p',has_text='Saved while you were away.')).to_be_visible()
        # A failed send retains its client identifier and can be retried once.
        alex.route('**/api/v1/messages',lambda route:route.abort())
        alex.get_by_label('Your message').fill('A message worth retrying.')
        alex.get_by_role('button',name='Send message',exact=True).click()
        expect(alex.get_by_role('button',name='Retry send')).to_be_visible()
        alex.unroute('**/api/v1/messages')
        alex.get_by_role('button',name='Retry send').click()
        expect(jordan.locator('.message-bubble p',has_text='A message worth retrying.')).to_be_visible()
        assert len([m for m in request('GET',f"/messages/{accounts[1]['user']['id']}",accounts[0]['access_token']) if m['body']=='A message worth retrying.']) == 1
        screenshot(alex,'messages-desktop.png')

        alex.goto(WEB + f"/sessions?swap={swap['id']}&user={accounts[1]['user']['id']}")
        expect(alex.get_by_label('Exchange partner')).to_have_value(str(swap['id']))
        local = datetime.now(timezone(timedelta(hours=5,minutes=30))) + timedelta(minutes=5)
        alex.get_by_label('What will you learn?').fill('React hooks, together')
        alex.get_by_label('Date',exact=True).fill(local.strftime('%Y-%m-%d'))
        alex.get_by_label('Time',exact=True).fill(local.strftime('%H:%M'))
        alex.get_by_role('button',name='Review booking').click()
        expect(alex.get_by_role('dialog')).to_be_visible()
        alex.get_by_role('button',name='Confirm booking').click()
        expect(alex.locator('.booking-card h3',has_text='React hooks, together')).to_be_visible()
        session = request('GET','/sessions',accounts[0]['access_token'])[0]
        screenshot(alex,'sessions-desktop.png')
        # A third account is refused even when it knows the session URL.
        outsider.goto(WEB + f"/sessions/{session['id']}/call")
        expect(outsider.get_by_text('This room is unavailable.')).to_be_visible()
        alex.get_by_role('link',name='Join session',exact=True).click()
        jordan.goto(WEB + f"/sessions/{session['id']}/call")
        for page in (alex,jordan):
            page.get_by_role('button',name='Check camera & microphone').click()
            page.wait_for_function("document.querySelector('.preview-tile video')?.videoWidth > 0")
            page.get_by_role('button',name='Join learning session').click()
        for page in (alex,jordan):
            expect(page.locator('.call-state')).to_have_text('You’re connected',timeout=25000)
            page.wait_for_function("document.querySelector('.remote-tile video')?.videoWidth > 0 && document.querySelector('.remote-tile video').currentTime > 0")
        alex.evaluate('window.testSockets.at(-1).close(4000)')
        expect(jordan.locator('.call-state')).to_contain_text('Waiting',timeout=10000)
        for page in (alex,jordan):
            expect(page.locator('.call-state')).to_have_text('You’re connected',timeout=25000)
            page.wait_for_function("document.querySelector('.remote-tile video')?.videoWidth > 0")
        alex.get_by_role('button',name='Mute microphone',exact=True).click()
        expect(alex.get_by_role('button',name='Unmute microphone',exact=True)).to_have_attribute('aria-pressed','true')
        alex.get_by_role('button',name='Turn camera off',exact=True).click()
        expect(alex.get_by_role('button',name='Turn camera on',exact=True)).to_have_attribute('aria-pressed','true')
        alex.get_by_role('button',name='Turn camera on',exact=True).click()
        alex.get_by_role('button',name='Unmute microphone',exact=True).click()
        screenshot(alex,'call-desktop.png')
        alex.get_by_role('button',name='Leave call',exact=True).click()
        expect(alex.get_by_text('A little wiser than before.')).to_be_visible()
        expect(jordan.locator('.call-state')).to_contain_text('Waiting for')
        alex.get_by_role('button',name='Rejoin session',exact=True).click()
        expect(alex.locator('.call-state')).to_have_text('You’re connected',timeout=25000)
        for page in (alex,jordan):
            page.get_by_role('button',name='Leave call',exact=True).click()
            page.goto(WEB + '/sessions')
        # Move this disposable fixture to its start so completion needs no wall-clock wait.
        with sqlite3.connect(database) as db:
            db.execute('UPDATE learning_sessions SET scheduled_at=? WHERE id=?',((datetime.now(timezone.utc)-timedelta(minutes=2)).replace(tzinfo=None).isoformat(sep=' '),session['id']))
        alex.reload()
        alex.get_by_role('button',name='Complete',exact=True).click()
        alex.get_by_role('button',name='Complete session',exact=True).click()
        expect(alex.locator('.booking-card .status.completed')).to_be_visible()
        alex.get_by_role('link',name='Review exchange').click()
        expect(alex.get_by_role('dialog')).to_be_visible()
        alex.get_by_label('Your reflection (optional)').fill('A thoughtful session with clear examples.')
        alex.get_by_role('button',name='Share review').click()
        expect(alex.get_by_text('Review shared',exact=True)).to_be_visible()

        for width in (390,768,1440):
            alex.set_viewport_size({'width':width,'height':900})
            for route in ('/','/sessions',f"/messages/{accounts[1]['user']['id']}",'/swaps','/profile','/feed'):
                alex.goto(WEB + route)
                alex.locator('main').wait_for()
                page_loading=alex.locator('main .loading')
                if page_loading.count():
                    expect(page_loading).to_have_count(0)
                no_overflow(alex)
                if width==390 and route in ('/','/sessions'):
                    screenshot(alex,'landing-mobile.png' if route=='/' else 'sessions-mobile.png')
            if width==390:
                alex.goto(WEB + f"/messages/{accounts[1]['user']['id']}")
                expect(alex.locator('.inbox-chat')).to_be_visible()
                expect(alex.locator('.message-bubble p').first).to_be_visible()
                screenshot(alex,'messages-mobile.png')
                alex.get_by_role('button',name='Back to conversations').click()
                expect(alex.locator('.inbox-sidebar')).to_be_visible()
                alex.get_by_role('button',name='Open navigation',exact=True).click()
                expect(alex.locator('#navigation-menu').get_by_role('link',name='Sessions',exact=True)).to_be_visible()
        assert not errors, json.dumps(errors,indent=2)
        print(json.dumps({'result':'passed','checks':['login','create skill','swap proposal and acceptance','live two-way chat','unread and read receipts','booking confirmation','private room denial','two-browser WebRTC media','mic/camera controls','leave/rejoin','completion/review','390/768/1440 responsive pages','mobile navigation'],'page_errors':errors,'screenshots':str(ARTIFACTS)},indent=2))
        browser.close()
finally:
    for process in reversed(processes):
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=5)
    for log in logs:
        log.close()
