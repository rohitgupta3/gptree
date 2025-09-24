Need to set these environment variables:
DATABASE_URL
FIREBASE_CLIENT_EMAIL
FIREBASE_CLIENT_ID
FIREBASE_PRIVATE_KEY_BASE64
FIREBASE_PRIVATE_KEY_ID
FIREBASE_PROJECT_ID
GEMINI_API_KEY
TEST_DATABASE_URL
USE_GEMINI

Then (in prod) need to build as per REPO_ROOT/package.json or (in dev) run `npm i` then `npm run dev` from the javascript directory
And need to install as per uv.lock (and pyproject.toml) via uv and (in prod) run the Procfile command or (in dev) run `PYTHONPATH=$PYTHONPATH:python uv run uvicorn python.web.app:app --reload`
