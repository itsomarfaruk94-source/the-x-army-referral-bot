import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select, func
from app.config import BOT_TOKEN, ADMIN_IDS, REFERRAL_REWARD, PACKAGES, BOT_USERNAME
from app.db import init_db, get_session, User, Referral, PointTransaction, ForceChannel, Product, KeyItem, Order, RedeemCode, RedeemUse

dp = Dispatcher()

def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="👤 Profile"), KeyboardButton(text="🔗 Refer & Earn")],
        [KeyboardButton(text="🎟️ Redeem Code"), KeyboardButton(text="🔑 Get Key")],
        [KeyboardButton(text="🛒 Shop Now"), KeyboardButton(text="🗝️ My Keys")]
    ], resize_keyboard=True)

def join_markup(channels):
    rows = [[InlineKeyboardButton(text=f"Join {c.title}", url=c.invite_link)] for c in channels]
    rows.append([InlineKeyboardButton(text="✅ Verify Join", callback_data="verify_join")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_user(session, tid):
    return session.scalar(select(User).where(User.telegram_id == tid))

async def check_membership(bot, tid):
    with get_session() as s:
        channels = s.scalars(select(ForceChannel).where(ForceChannel.active == True)).all()
    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch.chat_id, tid)
            if member.status not in ("member", "administrator", "creator"):
                missing.append(ch)
        except Exception:
            missing.append(ch)
    return missing

async def show_home(message, bot):
    missing = await check_membership(bot, message.from_user.id)
    if missing:
        await message.answer("🔒 বট ব্যবহার করতে নিচের সব Channel-এ Join করুন, তারপর Verify চাপুন।", reply_markup=join_markup(missing))
    else:
        await message.answer("🎮 Welcome to The X-Army Referral Bot!\n\nবন্ধু Invite করে Points আয় করুন এবং Points দিয়ে Key কিনুন।", reply_markup=main_menu())

@dp.message(CommandStart())
async def start(message: Message, bot: Bot):
    if not BOT_TOKEN:
        return
    tid = message.from_user.id
    payload = (message.text or "").split(maxsplit=1)
    referrer = None
    if len(payload) > 1 and payload[1].isdigit():
        candidate = int(payload[1])
        if candidate != tid:
            referrer = candidate
    with get_session() as s:
        user = get_user(s, tid)
        if not user:
            user = User(telegram_id=tid, username=message.from_user.username or "", full_name=message.from_user.full_name or "", referred_by=referrer)
            s.add(user)
            s.commit()
            if referrer and get_user(s, referrer):
                s.add(Referral(referrer_id=referrer, referred_user_id=tid, rewarded=False))
                s.commit()
        else:
            user.username = message.from_user.username or ""
            user.full_name = message.from_user.full_name or ""
            s.commit()
        if user.is_blocked:
            await message.answer("⛔ আপনার অ্যাকাউন্টটি Block করা হয়েছে।")
            return
    await show_home(message, bot)

@dp.callback_query(F.data == "verify_join")
async def verify_join(call: CallbackQuery, bot: Bot):
    missing = await check_membership(bot, call.from_user.id)
    if missing:
        await call.answer("সব Channel-এ Join করে আবার Verify করুন।", show_alert=True)
        await call.message.edit_reply_markup(reply_markup=join_markup(missing))
        return
    with get_session() as s:
        ref = s.scalar(select(Referral).where(Referral.referred_user_id == call.from_user.id))
        if ref and not ref.rewarded:
            referrer = get_user(s, ref.referrer_id)
            if referrer and not referrer.is_blocked:
                referrer.points += REFERRAL_REWARD
                s.add(PointTransaction(telegram_id=ref.referrer_id, amount=REFERRAL_REWARD, reason=f"Valid referral: {call.from_user.id}"))
                ref.rewarded = True
                s.commit()
                try:
                    await bot.send_message(ref.referrer_id, f"🎉 নতুন Valid Referral! +{REFERRAL_REWARD} Points যোগ হয়েছে।")
                except Exception:
                    pass
    await call.answer("Verification successful!")
    await call.message.answer("✅ Verification successful. Welcome!", reply_markup=main_menu())

@dp.message(F.text == "👤 Profile")
async def profile(message: Message):
    with get_session() as s:
        u = get_user(s, message.from_user.id)
        if not u:
            return await message.answer("প্রথমে /start দিন।")
        refs = s.scalar(select(func.count(Referral.id)).where(Referral.referrer_id == u.telegram_id, Referral.rewarded == True)) or 0
        await message.answer(f"💰 Your Account\n\n👤 Name: {u.full_name}\n🆔 User ID: {u.telegram_id}\n💎 Balance: {u.points} Points\n👥 Valid Referrals: {refs}")

@dp.message(F.text == "🔗 Refer & Earn")
async def refer(message: Message, bot: Bot):
    username = BOT_USERNAME
    if not username:
        me = await bot.get_me()
        username = me.username
    with get_session() as s:
        refs = s.scalar(select(func.count(Referral.id)).where(Referral.referrer_id == message.from_user.id, Referral.rewarded == True)) or 0
    await message.answer(f"🔗 Your Referral Link\nhttps://t.me/{username}?start={message.from_user.id}\n\n👥 Valid Referrals: {refs}\n🎁 Earn {REFERRAL_REWARD} points for each valid verified referral.")

@dp.message(F.text.in_({"🔑 Get Key", "🛒 Shop Now"}))
async def shop(message: Message):
    with get_session() as s:
        products = s.scalars(select(Product).where(Product.active == True).order_by(Product.sort_order, Product.id)).all()
        rows = [[InlineKeyboardButton(text=f"🛍️ {product.name}", callback_data=f"product:{product.id}")] for product in products]
    if not rows:
        return await message.answer("এখন কোনো Product উপলব্ধ নেই। পরে আবার চেষ্টা করুন।")
    await message.answer("🔑 Select a Product / Panel:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@dp.callback_query(F.data.startswith("product:"))
async def select_product(call: CallbackQuery):
    try:
        product_id = int(call.data.split(":", 1)[1])
    except ValueError:
        return await call.answer("Invalid product.", show_alert=True)
    with get_session() as s:
        product = s.get(Product, product_id)
        if not product or not product.active:
            return await call.answer("এই Product এখন উপলব্ধ নেই।", show_alert=True)
        rows = [[InlineKeyboardButton(text=f"{name} — {price} Points", callback_data=f"buy:{product.id}:{name}")] for name, price in PACKAGES.items()]
        title = product.name
    await call.message.answer(f"🛍️ {title}\n\nআপনার Key Duration নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()

@dp.callback_query(F.data.startswith("buy:"))
async def buy_key(call: CallbackQuery):
    try:
        _, product_raw, package = call.data.split(":", 2)
        product_id = int(product_raw)
    except ValueError:
        return await call.answer("Invalid purchase request.", show_alert=True)
    price = PACKAGES.get(package)
    if price is None:
        return await call.answer("Unknown package.", show_alert=True)
    with get_session() as s:
        u = get_user(s, call.from_user.id)
        product = s.get(Product, product_id)
        if not u or u.is_blocked:
            return await call.answer("Account unavailable.", show_alert=True)
        if not product or not product.active:
            return await call.answer("এই Product এখন উপলব্ধ নেই।", show_alert=True)
        key = s.scalar(select(KeyItem).where(KeyItem.product_id == product_id, KeyItem.package_name == package, KeyItem.sold == False).limit(1).with_for_update())
        if not key:
            return await call.answer("এই Product/Package-এর Key Stock শেষ। পরে চেষ্টা করুন।", show_alert=True)
        if u.points < price:
            return await call.answer(f"আপনার {price-u.points} Points কম আছে।", show_alert=True)
        u.points -= price
        key.sold = True
        key.sold_to = u.telegram_id
        s.add(PointTransaction(telegram_id=u.telegram_id, amount=-price, reason=f"Purchased {product.name} / {package} key"))
        s.add(Order(telegram_id=u.telegram_id, product_name=product.name, package_name=package, points_spent=price, key_value=key.key_value))
        s.commit()
        value, product_name = key.key_value, product.name
    await call.answer("Purchase successful!")
    await call.message.answer(f"🎉 Purchase Successful!\n\n🛍️ Product: {product_name}\n📦 Package: {package}\n🔑 Your Key:\n`{value}`\n\n⚠️ Keep your key private.", parse_mode="Markdown")

@dp.message(F.text == "🗝️ My Keys")
async def my_keys(message: Message):
    with get_session() as s:
        orders = s.scalars(select(Order).where(Order.telegram_id == message.from_user.id).order_by(Order.id.desc()).limit(20)).all()
        if not orders:
            return await message.answer("এখনো কোনো Key Purchase করেননি।")
        body = "\n\n".join([f"🛍️ {o.product_name}\n📦 {o.package_name}\n🔑 `{o.key_value}`" for o in orders])
    await message.answer("🗝️ Your Keys\n\n" + body, parse_mode="Markdown")

@dp.message(F.text == "🎟️ Redeem Code")
async def redeem_prompt(message: Message):
    await message.answer("আপনার Redeem Code পাঠান। Cancel করতে /cancel লিখুন।")

@dp.message(Command("cancel"))
async def cancel(message: Message):
    await message.answer("Cancelled.", reply_markup=main_menu())

@dp.message(F.text)
async def redeem_code(message: Message):
    code = message.text.strip().upper()
    if code.startswith("/") or code in {"👤 PROFILE", "🔗 REFER & EARN", "🎟️ REDEEM CODE", "🔑 GET KEY", "🛒 SHOP NOW", "🗝️ MY KEYS"}:
        return
    with get_session() as s:
        u = get_user(s, message.from_user.id)
        if not u:
            return
        rc = s.scalar(select(RedeemCode).where(RedeemCode.code == code, RedeemCode.active == True))
        if not rc:
            return await message.answer("❌ Invalid or expired Redeem Code.")
        if rc.uses >= rc.max_uses:
            return await message.answer("❌ This Redeem Code has reached its usage limit.")
        used = s.scalar(select(RedeemUse).where(RedeemUse.code_id == rc.id, RedeemUse.telegram_id == u.telegram_id))
        if used:
            return await message.answer("❌ আপনি এই Code আগে ব্যবহার করেছেন।")
        rc.uses += 1
        u.points += rc.points
        s.add(RedeemUse(code_id=rc.id, telegram_id=u.telegram_id))
        s.add(PointTransaction(telegram_id=u.telegram_id, amount=rc.points, reason=f"Redeem code: {code}"))
        s.commit()
    await message.answer(f"✅ Redeem Successful! +{rc.points} Points যোগ হয়েছে।")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Copy .env.example to .env and set BOT_TOKEN.")
    init_db()
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
