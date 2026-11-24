# The X-Army Referral Bot

এটি একটি প্রাথমিক Production-oriented project starter: Telegram bot + web admin + database।
এখনো আপনার নিজের BotFather token, Admin ID, Force Join channel এবং Key stock যোগ করতে হবে।

## 1) যা যা লাগবে
- Telegram account
- @BotFather থেকে তৈরি করা Bot Token
- আপনার Telegram numeric User ID (যেমন @userinfobot থেকে)
- Force Join channel-গুলোর username বা numeric chat ID
- Key stock (প্রতি লাইনে একটি Key)

## 2) Android ফোনে লোকালি টেস্ট (Termux)
1. F-Droid থেকে Termux ইনস্টল করুন।
2. Termux-এ চালান:
   `pkg update && pkg install python git unzip`
3. ZIP ফাইলটি Termux-এ আনজিপ করুন।
4. Project folder-এ ঢুকে চালান:
   `python -m venv .venv`
   `source .venv/bin/activate`
   `pip install -r requirements.txt  # Android/local SQLite setup`
5. `.env.example` কপি করে `.env` বানান এবং তথ্য পূরণ করুন:
   `cp .env.example .env`
6. Admin website চালু করুন:
   `uvicorn app.web:app --host 0.0.0.0 --port 8000`
7. নতুন Termux session-এ Bot চালু করুন:
   `python -m app.bot`
8. একই ফোনে browser-এ `http://127.0.0.1:8000` খুলুন।

## 3) BotFather setup
- Telegram-এ @BotFather খুলুন, `/newbot` দিন।
- Bot name: The X-Army Referral Bot
- Username অবশ্যই unique হতে হবে এবং `bot` দিয়ে শেষ হবে।
- Token কপি করে `.env`-এর BOT_TOKEN-এ দিন।
- Token কাউকে পাঠাবেন না বা public screenshot দেবেন না।

## 4) Force Join channel setup
- প্রতিটি Channel-এ আপনার bot-কে Admin করুন।
- Admin Dashboard > Add Force Join Channel-এ:
  - Chat ID: `@YourChannelUsername` অথবা `-100...`
  - Title: প্রদর্শনের নাম
  - Invite Link: `https://t.me/YourChannelUsername`
- Private channel হলে সঠিক invite link এবং numeric chat ID দিন।
- Bot-কে Admin না করলে Telegram সদস্য যাচাই করতে পারবে না।

## 5) Manual Key upload
Admin Dashboard > Product / Panel Management থেকে পাঁচটি প্রাথমিক Panel-এর নাম Rename করুন অথবা নতুন Product যোগ করুন।
এরপর Add Manual Keys-এ Product নির্বাচন করুন।
- Package নাম হুবহু `1 Hour`, `2 Hours`, অথবা `3 Hours` দিন।
- প্রতি লাইনে একটি করে Key পেস্ট করুন।
- একই Key দ্বিতীয়বার যোগ হবে না।

## 6) Product / Panel System
- Get Key চাপলে Active Product/Panel-এর তালিকা দেখাবে।
- Admin Dashboard থেকে Product যোগ, Rename, Hide/Show করা যাবে।
- প্রতিটি Product-এর Key Stock আলাদা; প্রতিটি Product-এ 1/2/3 Hour package রাখা যাবে।
- প্রথমবার Database তৈরি হলে Panel 1 থেকে Panel 5 নামে পাঁচটি editable placeholder তৈরি হবে।

## 7) Admin Dashboard
- URL: `http://127.0.0.1:8000` (local test)
- `.env`-এ ADMIN_USERNAME, ADMIN_PASSWORD পরিবর্তন করুন।
- ADMIN_IDS-এ নিজের Telegram numeric ID দিন।
- Public hosting-এ HTTPS ছাড়া Admin Panel ব্যবহার করবেন না।

## 8) VPS deployment (Docker)
1. Ubuntu VPS নিন এবং Docker + Docker Compose install করুন।
2. Production dependencies Dockerfile-এর মাধ্যমে স্বয়ংক্রিয়ভাবে install হবে (`requirements-prod.txt`)।
2. Project server-এ upload/unzip করুন।
3. `.env.example` কপি করে `.env` করুন।
4. `.env`-এ BOT_TOKEN, ADMIN_IDS, ADMIN_USERNAME, ADMIN_PASSWORD পূরণ করুন।
5. `DB_PASSWORD` নামে একটি শক্তিশালী database password `.env`-এ যোগ করুন।
6. `DATABASE_URL`-এর SQLite value বদলানোর দরকার নেই; Docker Compose container-এ PostgreSQL URL সেট করে।
7. চালান: `docker compose up -d --build`
8. Logs: `docker compose logs -f bot` এবং `docker compose logs -f web`
9. Production-এ domain + HTTPS reverse proxy (যেমন Caddy/Nginx) বসান এবং port 8000 সরাসরি public না রাখাই ভালো।

## গুরুত্বপূর্ণ
- Referral reward কেবল নতুন ইউজার প্রথমবার Verify Join সফল করলে একবার দেওয়া হয়।
- নিজের referral link ব্যবহার করে self-referral গ্রহণ করা হয় না।
- Key purchase-এর আগে পর্যাপ্ত point ও stock যাচাই করা হয়।
- SQLite শুধু local testing-এর জন্য; production-এ PostgreSQL ব্যবহার করুন।
- এই starter-এ Admin Panel HTTP Basic Auth ব্যবহার করে। Public production-এ অবশ্যই HTTPS, শক্তিশালী password, firewall, backup এবং rate limiting যোগ করুন।
- Bot এবং Web একই database ব্যবহার করে, তাই দুটো process চালু থাকতে হবে।
- প্রথম deployment-এর আগে test bot ও test keys দিয়ে end-to-end পরীক্ষা করুন।

## Broadcast (Admin Panel)
Admin Dashboard-এর Broadcast Message ফর্ম থেকে সব Unblocked সদস্যকে Text, Photo + Caption, অথবা Video + Caption পাঠানো যাবে। ছবি/ভিডিও সর্বোচ্চ 20 MB; media caption সর্বোচ্চ 1024 অক্ষর। Bot Token সঠিকভাবে সেট থাকতে হবে এবং সদস্য আগে বট Start করে থাকতে হবে। Telegram-এ যেসব সদস্য বট Block করেছেন বা বটকে Start করেননি তাদের কাছে পাঠানো যাবে না; ব্যর্থতার সংখ্যা রিপোর্ট হবে। বড় audience-এ Telegram rate limits প্রযোজ্য।
