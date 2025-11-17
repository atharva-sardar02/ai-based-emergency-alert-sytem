# 🗺️ Fix: Map Showing "0 alerts" - Solution

## ✅ Problem Fixed!

I've backfilled coordinates for 215 existing alerts. The map should now work!

## 🔧 What Was Done

1. **Created backfill script** that extracts coordinates from existing alerts' `raw_payload`
2. **Ran the backfill** - 215 alerts now have coordinates
3. **Added debug logging** to map page to help troubleshoot

## 📋 Next Steps

### 1. Refresh Your Browser
- Hard refresh the map page (Ctrl+F5 or Ctrl+Shift+R)
- Or close and reopen http://localhost:3000/map.html

### 2. Check Browser Console
- Open browser Developer Tools (F12)
- Check Console tab for debug messages
- Should see: "Fetched X alerts from API" and "X alerts have coordinates"

### 3. Verify API Returns Coordinates
Test the API directly:
```
http://localhost:8000/api/alerts?limit=10
```

You should see `latitude` and `longitude` fields in the response.

### 4. If Still Showing 0 Alerts

Run this to check database:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from app.database import SessionLocal; from app.models import Alert; db = SessionLocal(); total = db.query(Alert).count(); with_coords = db.query(Alert).filter(Alert.latitude.isnot(None), Alert.longitude.isnot(None)).count(); print(f'Total: {total}, With coords: {with_coords}'); db.close()"
```

Should show: `Total: 235, With coords: 215`

### 5. Re-run Backfill (if needed)
If coordinates are missing:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m app.utils.backfill_coordinates
```

## 🎯 Expected Result

After refreshing:
- Map should show markers for alerts
- Stats should show "X visible alerts, X total with location"
- You can click markers to see alert details

## 📍 Note About Alert Locations

If you're in **TEST_MODE=true**:
- Many alerts will be from far away (global earthquakes, Virginia-wide weather)
- Zoom out on the map to see them all
- The map auto-fits to show all markers

If you want Alexandria-specific alerts:
- Set `TEST_MODE=false` in `backend/.env`
- Re-run ingestion to get local alerts only

---

## ❓ Still Not Working?

1. **Check browser console** for errors
2. **Verify API is running**: http://localhost:8000/api/health
3. **Check API response** includes latitude/longitude
4. **Restart backend** if needed

The backfill successfully added coordinates to 215 alerts, so they should appear on the map now! 🎉







