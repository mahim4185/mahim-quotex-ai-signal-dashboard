# Mahim Quotex AI Signal Dashboard — GitHub Build Package

এই রিপোজিটরিতে আগের V4 Dashboard-এর মূল ফাইলগুলো `dashboard/` ফোল্ডারে রাখা হয়েছে। মূল সোর্স ফাইল পরিবর্তন না করে Render deployment blueprint এবং GitHub Actions syntax-check যোগ করা হয়েছে।

## Render deployment
1. ZIP extract করে এর ভেতরের সব ফাইল GitHub repository-র root-এ upload করুন (ZIP ফাইলটিকে শুধু upload করলে হবে না)।
2. Render-এ New + > Blueprint নির্বাচন করে এই repository connect করুন; অথবা Web Service বানিয়ে root directory `dashboard` দিন।
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Health check path: `/api/health`

## গুরুত্বপূর্ণ সীমাবদ্ধতা ও সতর্কতা
- এটি আগের V4 dashboard-এর source preservation + deployment package; নতুন Vision AI chart-image analysis এখানে বাস্তবায়িত নয়।
- বর্তমান V4 signal logic rule-based technical indicators ব্যবহার করে এবং market feed Biquote endpoint থেকে নেয়; এটি Quotex-এর নিজস্ব feed নয়।
- Quotex OTC chart বা broker account integration আছে বলে ধরে নেবেন না।
- CALL/PUT/WAIT কোনো নিশ্চিত পূর্বাভাস নয়। score বা confidence-কে win probability ভাববেন না।
- Demo account-এ পরীক্ষা করুন। অন্তত 200টি logged signal এবং বিভিন্ন market condition না পরীক্ষা করে real-money ব্যবহার করবেন না।
- Render-এর ephemeral filesystem-এ SQLite history deploy/restart-এ হারিয়ে যেতে পারে। স্থায়ী history দরকার হলে persistent disk বা managed PostgreSQL যুক্ত করতে হবে।
- এই package-এ কোনো broker login, password, OTP, auto-trading বা trade execution নেই।

## কী কী আছে
- `dashboard/`: আগের V4 FastAPI backend এবং web UI।
- `render.yaml`: Render Blueprint configuration।
- `.github/workflows/ci.yml`: push/PR-এ Python dependency install ও syntax check।
- `.gitignore`: local secrets, cache এবং database file ignore।

## Validation status
Package structure এবং Python syntax CI configuration প্রস্তুত করা হয়েছে। এখানে Render account-এ deploy, external Biquote endpoint live test, browser UI end-to-end test, বা Quotex chart verification করা হয়নি। তাই একে 100% live-verified বলা যাবে না।
