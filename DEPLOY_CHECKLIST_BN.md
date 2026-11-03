# Render Build Checklist

- [ ] ZIP extract করা হয়েছে।
- [ ] ZIP-এর ভেতরের সব ফাইল repository root-এ upload করা হয়েছে।
- [ ] `render.yaml` root-এ আছে।
- [ ] Render Blueprint repository connect করা হয়েছে।
- [ ] Deploy logs-এ dependency install ও Uvicorn start সফল।
- [ ] `https://YOUR-SERVICE.onrender.com/api/health` থেকে healthy response এসেছে।
- [ ] Dashboard browser-এ খোলা হয়েছে।
- [ ] প্রতিটি supported pair/timeframe-এর data fetch আলাদাভাবে পরীক্ষা করা হয়েছে।
- [ ] Demo-only signal logging ও outcome entry পরীক্ষা করা হয়েছে।

**নোট:** health endpoint কাজ করলেই market feed বা signal accuracy যাচাই হয়ে যায় না।
