from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select, func
from aiogram import Bot
from aiogram.types import BufferedInputFile
import secrets, asyncio
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD
from app.db import init_db, get_session, User, Referral, KeyItem, Order, ForceChannel, RedeemCode, PointTransaction, Product

app = FastAPI(title="The X-Army Referral Bot Admin")
security = HTTPBasic()

def auth(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    ok_pass = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (ok_user and ok_pass) or not ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

@app.on_event("startup")
def startup():
    init_db()

def page(content):
    return HTMLResponse(f'''<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>X-Army Admin</title><style>
    body{{margin:0;background:#061d3a;color:#eaf5ff;font:15px Arial}}.wrap{{max-width:1000px;margin:auto;padding:20px}}
    h1,h2{{color:#fff}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
    .card,form{{background:#102c4d;border:1px solid #1762a0;border-radius:14px;padding:16px;margin:12px 0}}
    input,button{{box-sizing:border-box;width:100%;padding:12px;margin:6px 0;border-radius:8px;border:1px solid #3679ad}}
    input{{background:#071b30;color:white}}button{{background:#008fe8;color:white;font-weight:bold;border:0}}
    a{{color:#5bc0ff}}small{{color:#a9c7df}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #285174;text-align:left}}
    </style></head><body><div class="wrap">{content}</div></body></html>''')

@app.get("/", response_class=HTMLResponse)
def dashboard(_: str = Depends(auth)):
    with get_session() as s:
        users = s.scalar(select(func.count(User.id))) or 0
        refs = s.scalar(select(func.count(Referral.id)).where(Referral.rewarded == True)) or 0
        sold = s.scalar(select(func.count(Order.id))) or 0
        stock = s.scalar(select(func.count(KeyItem.id)).where(KeyItem.sold == False)) or 0
        points = s.scalar(select(func.coalesce(func.sum(User.points), 0))) or 0
        channels = s.scalars(select(ForceChannel)).all()
        products = s.scalars(select(Product).order_by(Product.sort_order, Product.id)).all()
        codes = s.scalars(select(RedeemCode).order_by(RedeemCode.id.desc()).limit(10)).all()
        recent = s.scalars(select(Order).order_by(Order.id.desc()).limit(10)).all()
    content = f'''<h1>⚡ THE X-ARMY ADMIN</h1><p>Referral Bot Control Center</p>
    <div class="grid">
    <div class="card"><small>Total Users</small><h2>{users}</h2></div>
    <div class="card"><small>Valid Referrals</small><h2>{refs}</h2></div>
    <div class="card"><small>Keys Sold</small><h2>{sold}</h2></div>
    <div class="card"><small>Available Keys</small><h2>{stock}</h2></div>
    <div class="card"><small>Users' Current Points</small><h2>{points}</h2></div></div>
    <div class="grid">
    <section><form method="post" action="/broadcast" enctype="multipart/form-data"><h2>📣 Broadcast Message</h2>
    <textarea name="caption" placeholder="আপডেট / Announcement লিখুন" required style="width:100%;height:110px;background:#071b30;color:white"></textarea>
    <input type="file" name="media" accept="image/*,video/*">
    <small>ঐচ্ছিক: একটি ছবি অথবা ভিডিও যুক্ত করতে পারবেন। শুধু Text পাঠাতেও পারবেন।</small>
    <button>Send Broadcast to All Members</button></form>
    <form method="post" action="/products/add"><h2>🛍️ Add New Product / Panel</h2>
    <input name="name" placeholder="Product name" required>
    <input name="description" placeholder="Short description (optional)">
    <button>Add Product</button></form>
    <form method="post" action="/keys/add"><h2>➕ Add Manual Keys</h2>
    <select name="product_id" required style="width:100%;padding:12px;background:#071b30;color:white">{''.join(f'<option value="{p.id}">{p.name}</option>' for p in products if p.active)}</select>
    <input name="package_name" placeholder="Package: 1 Hour / 2 Hours / 3 Hours" required>
    <textarea name="keys" placeholder="Paste one key per line" required style="width:100%;height:120px;background:#071b30;color:white"></textarea>
    <button>Add Keys</button></form>
    <form method="post" action="/channels/add"><h2>📢 Add Force Join Channel</h2>
    <input name="chat_id" placeholder="@channelusername or -100..." required>
    <input name="title" placeholder="Channel display name" required>
    <input name="invite_link" placeholder="https://t.me/channelname" required><button>Add Channel</button></form>
    <form method="post" action="/codes/create"><h2>🎟️ Create Redeem Code</h2>
    <input name="code" placeholder="e.g. XARMY100" required>
    <input name="points" type="number" min="1" placeholder="Points" required>
    <input name="max_uses" type="number" min="1" placeholder="Maximum total uses" value="1" required><button>Create Code</button></form>
    <form method="post" action="/users/adjust"><h2>💎 Add / Deduct User Points</h2>
    <input name="telegram_id" type="number" placeholder="Telegram User ID" required>
    <input name="amount" type="number" placeholder="Use negative number to deduct" required>
    <input name="reason" placeholder="Reason" required><button>Update Points</button></form></section>
    <section><div class="card"><h2>🛍️ Product / Panel Management</h2>{''.join(f'<p><b>{p.name}</b> — {"Active" if p.active else "Hidden"} <a href="/products/toggle/{p.id}">{"Hide" if p.active else "Show"}</a> | <a href="/products/edit/{p.id}">Rename</a></p>' for p in products) or '<p>No products configured.</p>'}<small>পাঁচটি প্রাথমিক Panel তৈরি করা আছে। নাম পরিবর্তন করুন, বন্ধ করুন অথবা নতুন Product যোগ করুন।</small></div>
    <div class="card"><h2>📢 Force Join Channels</h2>{''.join(f'<p>{c.title} — {c.chat_id} <a href="/channels/delete/{c.id}">Remove</a></p>' for c in channels) or '<p>No channels configured.</p>'}</div>
    <div class="card"><h2>🎟️ Recent Redeem Codes</h2>{''.join(f'<p><b>{c.code}</b> — {c.points} pts — {c.uses}/{c.max_uses} uses</p>' for c in codes) or '<p>No codes yet.</p>'}</div>
    <div class="card"><h2>🧾 Recent Orders</h2>{''.join(f'<p>#{o.id} — User {o.telegram_id} — {o.package_name}</p>' for o in recent) or '<p>No orders yet.</p>'}</div>
    </section></div><p><a href="/users">View Users</a></p><small>Keep this admin URL private. Use HTTPS in production.</small>'''
    return page(content)


@app.post("/broadcast", response_class=HTMLResponse)
async def broadcast(caption: str = Form(...), media: UploadFile | None = File(None), _: str = Depends(auth)):
    message_text = caption.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Broadcast text is required")
    if len(message_text) > 4000:
        raise HTTPException(status_code=400, detail="Text is too long (maximum 4000 characters)")

    media_bytes = None
    media_name = None
    media_type = None
    if media and media.filename:
        media_bytes = await media.read()
        if len(media_bytes) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Media file must be 20 MB or smaller")
        media_name = media.filename
        content_type = (media.content_type or "").lower()
        if content_type.startswith("image/"):
            media_type = "photo"
        elif content_type.startswith("video/"):
            media_type = "video"
        else:
            raise HTTPException(status_code=400, detail="Only image or video files are supported")
        if len(message_text) > 1024:
            raise HTTPException(status_code=400, detail="Caption must be 1024 characters or fewer when media is attached")

    with get_session() as s:
        recipients = s.scalars(select(User.telegram_id).where(User.is_blocked == False)).all()
    if not recipients:
        return page("<h1>Broadcast</h1><p>No members to send to.</p><p><a href='/'>Back</a></p>")

    sent = 0
    failed = 0
    try:
        async with Bot(token=__import__('app.config', fromlist=['BOT_TOKEN']).BOT_TOKEN) as bot:
            for telegram_id in recipients:
                try:
                    if media_type == "photo":
                        await bot.send_photo(telegram_id, BufferedInputFile(media_bytes, filename=media_name), caption=message_text)
                    elif media_type == "video":
                        await bot.send_video(telegram_id, BufferedInputFile(media_bytes, filename=media_name), caption=message_text)
                    else:
                        await bot.send_message(telegram_id, message_text)
                    sent += 1
                except Exception:
                    failed += 1
                await asyncio.sleep(0.05)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Broadcast could not start: {type(exc).__name__}")

    return page(f"<h1>📣 Broadcast finished</h1><div class='card'><h2>Sent: {sent}</h2><h2>Failed: {failed}</h2><p>Total recipients: {len(recipients)}</p></div><p><a href='/'>Back to Dashboard</a></p>")

@app.post("/products/add")
def add_product(name: str = Form(...), description: str = Form(""), _: str = Depends(auth)):
    clean = name.strip()
    if clean:
        with get_session() as s:
            if not s.scalar(select(Product).where(Product.name == clean)):
                s.add(Product(name=clean, description=description.strip()[:250], sort_order=100))
                s.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/products/toggle/{product_id}")
def toggle_product(product_id: int, _: str = Depends(auth)):
    with get_session() as s:
        product = s.get(Product, product_id)
        if product:
            product.active = not product.active
            s.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/products/edit/{product_id}", response_class=HTMLResponse)
def edit_product_page(product_id: int, _: str = Depends(auth)):
    with get_session() as s:
        product = s.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        content = ("<h1>Rename Product</h1><form method='post' action='/products/edit/" + str(product_id) + "'>"
                   + "<input name='name' value='" + product.name + "' required>"
                   + "<input name='description' value='" + product.description + "'>"
                   + "<button>Save Product</button></form><p><a href='/'>Back to dashboard</a></p>")
        return page(content)

@app.post("/products/edit/{product_id}")
def edit_product(product_id: int, name: str = Form(...), description: str = Form(""), _: str = Depends(auth)):
    with get_session() as s:
        product = s.get(Product, product_id)
        clean = name.strip()
        duplicate = s.scalar(select(Product).where(Product.name == clean, Product.id != product_id)) if clean else None
        if product and clean and not duplicate:
            product.name = clean
            product.description = description.strip()[:250]
            s.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/keys/add")
def add_keys(product_id: int = Form(...), package_name: str = Form(...), keys: str = Form(...), _: str = Depends(auth)):
    values = [x.strip() for x in keys.splitlines() if x.strip()]
    if package_name.strip() not in {"1 Hour", "2 Hours", "3 Hours"}:
        raise HTTPException(status_code=400, detail="Package must be 1 Hour, 2 Hours, or 3 Hours")
    with get_session() as s:
        product = s.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        for value in values:
            if not s.scalar(select(KeyItem).where(KeyItem.key_value == value)):
                s.add(KeyItem(product_id=product_id, package_name=package_name.strip(), key_value=value))
        s.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/channels/add")
def add_channel(chat_id: str = Form(...), title: str = Form(...), invite_link: str = Form(...), _: str = Depends(auth)):
    with get_session() as s:
        existing = s.scalar(select(ForceChannel).where(ForceChannel.chat_id == chat_id.strip()))
        if existing:
            existing.title, existing.invite_link, existing.active = title.strip(), invite_link.strip(), True
        else:
            s.add(ForceChannel(chat_id=chat_id.strip(), title=title.strip(), invite_link=invite_link.strip()))
        s.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/channels/delete/{channel_id}")
def delete_channel(channel_id: int, _: str = Depends(auth)):
    with get_session() as s:
        c = s.get(ForceChannel, channel_id)
        if c:
            s.delete(c); s.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/codes/create")
def create_code(code: str = Form(...), points: int = Form(...), max_uses: int = Form(...), _: str = Depends(auth)):
    with get_session() as s:
        if not s.scalar(select(RedeemCode).where(RedeemCode.code == code.strip().upper())):
            s.add(RedeemCode(code=code.strip().upper(), points=points, max_uses=max_uses))
            s.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/users/adjust")
def adjust_user(telegram_id: int = Form(...), amount: int = Form(...), reason: str = Form(...), _: str = Depends(auth)):
    with get_session() as s:
        u = s.scalar(select(User).where(User.telegram_id == telegram_id))
        if u and u.points + amount >= 0:
            u.points += amount
            s.add(PointTransaction(telegram_id=telegram_id, amount=amount, reason=reason[:250]))
            s.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/users", response_class=HTMLResponse)
def users(_: str = Depends(auth)):
    with get_session() as s:
        rows = s.scalars(select(User).order_by(User.id.desc()).limit(100)).all()
    body = ''.join(f'<tr><td>{u.telegram_id}</td><td>{u.full_name}</td><td>{u.points}</td><td>{u.is_blocked}</td></tr>' for u in rows)
    return page('<h1>Users (latest 100)</h1><table><tr><th>Telegram ID</th><th>Name</th><th>Points</th><th>Blocked</th></tr>'+body+'</table><p><a href="/">Back</a></p>')
