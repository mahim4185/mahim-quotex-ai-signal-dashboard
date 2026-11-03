# Mahim Quotex AI Signal Dashboard — আপডেটেড সংস্করণ

## কী আছে
- Quotex Demo ID শুধু পরিচিতি/লেবেল হিসেবে সেভ করা যায়।
- Normal Forex-এর জন্য Twelve Data feed যুক্ত করার জায়গা।
- প্রতি ৬০ সেকেন্ডে স্বয়ংক্রিয় বিশ্লেষণ।
- CALL / PUT / WAIT এবং Signal History।
- OTC আলাদা করে দেখানো হয়; যাচাই করা Quotex OTC feed না থাকলে WAIT দেখায়।
- কোনো ট্রেড অটোমেটিক করে না।

## খুব গুরুত্বপূর্ণ
শুধু Quotex ID লিখলে Quotex অ্যাকাউন্টে লগইন বা মার্কেট ডেটা পাওয়া যায় না। এই ID কেবল ড্যাশবোর্ডে সেভ হয়। পাসওয়ার্ড/OTP কখনো দেবেন না।
Normal Forex লাইভ ডেটার জন্য Twelve Data API key দরকার। তাদের ফ্রি প্ল্যান/সীমা পরিবর্তিত হতে পারে। API key না দিলে ওয়েবসাইট লাইভ সিগন্যাল দেখাবে না, বরং WAIT দেখাবে।
OTC ডেটা Quotex-এর নিজস্ব এবং এই প্রজেক্টে কোনো ভুয়া OTC ডেটা ব্যবহার করা হয় না।

## GitHub + Render-এ আপডেট
1. ZIP Extract করুন।
2. GitHub-এ আপনার dashboard repository খুলুন।
3. পুরোনো ফাইলগুলোর জায়গায় এই ZIP-এর সব ফাইল আপলোড/Replace করুন। `static` ফোল্ডারসহ আপলোড করবেন।
4. Render-এ আগের Web Service থাকলে সেটি GitHub repository থেকে Auto Deploy করবে। না হলে New + → Web Service দিয়ে repository connect করুন।
5. Render-এর Environment-এ `TWELVE_DATA_API_KEY` নামে API key যোগ করুন (ঐচ্ছিক; লাইভ Forex data-এর জন্য)।
6. Deploy শেষ হলে Render URL খুলুন।

## API key কোথায় পাবেন
Twelve Data-এর অফিসিয়াল সাইটে account খুলে API key নিন: https://twelvedata.com/
API key কাউকে প্রকাশ করবেন না; GitHub-এ কোডের মধ্যে বসাবেন না। Render Environment Variables-এ রাখবেন।

## GitHub Pages
এই অ্যাপের Python backend GitHub Pages-এ চলে না। Render-এ deploy করতে হবে। GitHub Pages-এর URL একা ব্যবহার করলে Auto Signal backend কাজ করবে না।
