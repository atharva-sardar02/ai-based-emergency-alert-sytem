# 🗺️ Map Feature - Changes to Running Process

## ✅ What Changed

The map feature has been added, but **the running process is almost exactly the same**! There's just **one new step** you need to do once.

---

## 🚀 New Step (One-Time Only)

Before running the system for the first time with map features, you need to run the database migration:

```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the migration (this adds latitude/longitude columns)
alembic upgrade head
```

**That's it!** This only needs to be done once. After that, everything is the same as before.

---

## 📋 Running Process (Unchanged)

Everything else works exactly the same:

### Terminal A - Backend API
```powershell
./start-backend.ps1
```
**No changes** - works exactly as before

### Terminal B - Ingestion Scheduler
```powershell
./start-ingestion.ps1
```
**No changes** - works exactly as before  
**NEW**: Ingestion services now automatically extract and store coordinates

### Terminal C - Classification Worker
```powershell
./start-classifier.ps1
```
**No changes** - works exactly as before

### Terminal D - Frontend
```powershell
cd frontend
python -m http.server 3000
```
**No changes** - works exactly as before  
**NEW**: You can now access `map.html` at http://localhost:3000/map.html

---

## 🆕 What's New

1. **New Map Page**: 
   - Visit http://localhost:3000/map.html
   - Or click "Map View" button from the dashboard

2. **Coordinates Automatically Extracted**:
   - New alerts will automatically have coordinates (if available from source)
   - Old alerts won't have coordinates until you re-run ingestion

3. **Navigation**:
   - "List View" and "Map View" buttons added to both pages

---

## 📝 Important Notes

### For Existing Alerts
If you already have alerts in your database from before this update:
- They won't show up on the map initially (no coordinates stored)
- **Solution**: Re-run ingestion once to populate coordinates:
  ```powershell
  cd backend
  .\venv\Scripts\Activate.ps1
  python -m app.services.ingest_nws
  python -m app.services.ingest_usgs_eq
  python -m app.services.ingest_nwis
  ```
- Or just wait for the scheduler to fetch new data (which will have coordinates)

### For New Alerts
- All new alerts fetched after running the migration will automatically include coordinates
- No manual intervention needed!

---

## 🔄 Quick Start Summary

**First time with map feature:**
1. ✅ Run migration: `cd backend && .\venv\Scripts\Activate.ps1 && alembic upgrade head`
2. ✅ Start everything as usual (same as before)

**Every subsequent run:**
1. ✅ Start everything as usual (exactly the same as before)
2. ✅ No migration needed again

---

## 🗺️ Accessing the Map

Once everything is running:
- **List View**: http://localhost:3000/index.html (or just http://localhost:3000)
- **Map View**: http://localhost:3000/map.html
- **API Docs**: http://localhost:8000/docs (unchanged)

---

## ❓ FAQ

**Q: Do I need to change my .env file?**  
A: No, your existing `.env` works perfectly.

**Q: Will my existing alerts work?**  
A: Yes! They'll still show in the list view. They just won't appear on the map until you re-run ingestion.

**Q: Do I need to change how I run ingestion?**  
A: No! Ingestion works exactly the same. It just now also extracts coordinates automatically.

**Q: What if migration fails?**  
A: Make sure:
   - PostgreSQL is running (`docker-compose ps`)
   - You're in the `backend` directory
   - Virtual environment is activated
   - Database connection is correct in `.env`

---

## ✅ Summary

**Bottom line**: Run `alembic upgrade head` once, then everything is exactly the same as before! 🎉





