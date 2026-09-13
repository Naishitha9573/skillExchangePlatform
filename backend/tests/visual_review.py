"""Responsive UI review against an isolated, explicitly seeded database."""
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / '.artifacts' / 'visual'
ARTIFACTS.mkdir(parents=True, exist_ok=True)
WEB = 'http://127.0.0.1:5182'
API = 'http://127.0.0.1:8015/api/v1'
database = ARTIFACTS / f'review-{secrets.token_hex(5)}.db'
environment = {**os.environ, 'DATABASE_URL': f'sqlite:///{database.as_posix()}',
               'SECRET_KEY': secrets.token_urlsafe(48), 'DEMO_MODE': 'true',
               'CORS_ORIGINS': WEB, 'VITE_API_URL': API,
               'GEMINI_API_KEY': '', 'GOOGLE_CLIENT_ID': '', 'GOOGLE_CLIENT_SECRET': ''}
processes, logs, errors, overflows, checks = [], [], [], [], []


def start(command, cwd, name):
    log = (ARTIFACTS / f'{name}.log').open('w', encoding='utf-8')
    logs.append(log)
    processes.append(subprocess.Popen(command, cwd=cwd, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0))


def ready(url):
    for _ in range(100):
        try:
            if httpx.get(url, timeout=1).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(.2)
    raise RuntimeError('Server did not start: ' + url)


def inspect(page, route, width):
    page.goto(WEB + route, wait_until='networkidle')
    expect(page.locator('main')).to_be_visible()
    page.evaluate('document.fonts.ready')
    page.wait_for_timeout(300)
    overflow = page.evaluate('''() => {
      if(document.documentElement.scrollWidth<=innerWidth+1)return [];
      return [...document.querySelectorAll('main *,header *,footer *')].filter(e=>{
        const b=e.getBoundingClientRect();return b.width&&b.right>innerWidth+1&&getComputedStyle(e).position!=='absolute';
      }).slice(0,12).map(e=>({tag:e.tagName,class:e.className,right:e.getBoundingClientRect().right}));
    }''')
    if overflow:
        overflows.append({'width': width, 'route': route, 'elements': overflow})
    checks.append({'width': width, 'route': route})


try:
    seeded = subprocess.run([sys.executable, 'seed.py'], cwd=ROOT / 'backend', env=environment, capture_output=True, text=True)
    assert seeded.returncode == 0, seeded.stderr
    start([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8015'], ROOT / 'backend', 'api')
    start(['node', str(ROOT / 'frontend/node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', '5182', '--strictPort'], ROOT / 'frontend', 'web')
    ready(API.replace('/api/v1', '/health'))
    ready(WEB)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' and 'Warning:' in msg.text else None)
        inspect(page, '/', 1440)
        expect(page.locator('.popular-card')).to_have_count(6)
        expect(page.locator('.member-card')).to_have_count(6)
        expect(page.locator('.proof-metric').first).to_contain_text('20')
        page.screenshot(path=str(ARTIFACTS / 'landing-desktop.png'))
        for section in ['explore-skills', 'smart-matching', 'community', 'faq']:
            page.locator('#' + section).screenshot(path=str(ARTIFACTS / (section + '.png')))
        page.get_by_role('tab', name='Real-time chat', exact=True).click()
        expect(page.locator('.product-tab-panel .preview-chat')).to_be_visible()
        page.get_by_role('tab', name='Real-time chat', exact=True).press('ArrowRight')
        expect(page.get_by_role('tab', name='Session scheduling')).to_be_focused()
        expect(page.locator('.product-tab-panel .preview-schedule')).to_be_visible()
        page.get_by_role('button', name='Can we meet through video?').click()
        expect(page.get_by_role('button', name='Can we meet through video?')).to_have_attribute('aria-expanded', 'true')
        page.locator('.category-tabs').get_by_role('button', name='Design', exact=True).click()
        assert page.locator('.popular-card').count() > 0
        assert page.locator('.popular-card:not([data-category="Design"])').count() == 0
        page.locator('.popular-card a').first.click()
        page.wait_for_url('**/feed?search=*')
        expect(page.get_by_label('Search skills')).not_to_have_value('')
        for width in [1440,1280,1024,768,430,390]:
            page.set_viewport_size({'width': width, 'height': 900})
            for route in ['/', '/login', '/register', '/feed', '/feed?view=people', '/members/1']:
                inspect(page, route, width)
                if width in [1440,390] and route in ['/', '/login', '/feed?view=people']:
                    name = {'/':'landing','/login':'login','/feed?view=people':'people'}[route]
                    page.screenshot(path=str(ARTIFACTS / f'{name}-{width}.png'), full_page=route!='/')
            if width == 390:
                page.get_by_role('button', name='Open navigation', exact=True).click()
                expect(page.locator('#public-menu').get_by_role('link', name='How it works')).to_be_visible()
                page.locator('#public-menu').get_by_role('link', name='How it works').click()
                expect(page.locator('#public-menu')).to_have_count(0)
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(WEB+'/login')
        page.get_by_label('Email address').fill('ananya@demo.com')
        page.get_by_label('Password', exact=True).fill('demo123')
        page.get_by_role('button', name='Sign in', exact=True).click()
        page.wait_for_url('**/dashboard')
        for width in [1440,1280,1024,768,430,390]:
            page.set_viewport_size({'width': width, 'height': 900})
            for route in ['/dashboard','/add-skill','/skill/3','/profile','/swaps','/messages/2','/sessions','/sessions/7/call','/innovation','/coach','/leaderboard']:
                inspect(page,route,width)
                if width in [1440,390] and route in ['/dashboard','/sessions','/messages/2','/profile','/innovation']:
                    page.screenshot(path=str(ARTIFACTS / f'{route.strip("/").replace("/","-")}-{width}.png'), full_page=True)
        # No fabricated production figures or invisible content during an API failure.
        page.route('**/api/v1/community/**', lambda route: route.fulfill(status=503, body='{}', content_type='application/json'))
        inspect(page,'/',390)
        expect(page.get_by_text('The community is taking a moment.').first).to_be_visible()
        expect(page.locator('.proof-metric').first).to_contain_text('—')
        assert page.locator('[data-reveal]').evaluate_all('(nodes)=>nodes.every(n=>getComputedStyle(n).opacity==="1")')
        page.unroute('**/api/v1/community/**')
        page.get_by_role('button',name='Try again',exact=True).first.click()
        expect(page.locator('.member-card')).to_have_count(6)
        browser.close()
    report={'checks':checks,'overflows':overflows,'console_errors':errors,'screenshots':str(ARTIFACTS)}
    (ARTIFACTS/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'viewports_checked':len(checks),'overflows':overflows,'errors':errors,'artifacts':str(ARTIFACTS)},indent=2))
    assert not overflows and not errors
finally:
    for process in reversed(processes):
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    for log in logs:
        log.close()
