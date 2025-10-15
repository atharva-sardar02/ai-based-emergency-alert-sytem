# Testing New Data Sources

## 🔥 NASA FIRMS & 🚇 WMATA Integration Complete!

### What Was Added

1. **NASA FIRMS Fire Detection** ✅
   - Ingests satellite fire/thermal anomaly data
   - Uses API key from `.env`
   - Automatically skips if no API key configured
   - Works in TEST_MODE (Virginia) and production (Alexandria)

2. **WMATA Transit Incidents** ✅
   - Ingests metro rail and bus incidents
   - Uses API key from `.env`
   - Automatically skips if no API key configured
   - Shows service disruptions and delays

3. **Dynamic Source Display** ✅
   - Dashboard only shows sources with actual data
   - Updates automatically as alerts come in
   - No more hardcoded source list!

---

## 🧪 Test the New Sources

### 1. Add API Keys to `.env`

Edit `backend/.env`:

```env
# Add your keys here (see API_KEYS_INFO.md for how to get them)
FIRMS_API_KEY=your_nasa_firms_key_here
WMATA_API_KEY=your_wmata_key_here
```

### 2. Test Individual Sources

```bash
cd backend
.\venv\Scripts\Activate.ps1

# Test NASA FIRMS
python -m app.services.ingest_fires

# Test WMATA
python -m app.services.ingest_wmata
```

**Expected Output:**
```
Ingested X new fire detections
Ingested Y new WMATA incidents
```

### 3. Run All Sources Together

```bash
python -m app.services.ingest_scheduler
```

This will fetch from ALL 5 sources:
- ✅ NWS Weather
- ✅ USGS Earthquakes  
- ✅ USGS NWIS (Rivers)
- ✅ NASA FIRMS (Fires) - if API key set
- ✅ WMATA (Transit) - if API key set

### 4. Check Dashboard

Refresh http://localhost:3000

The **"Active Data Sources"** panel will now show:
- Only sources with actual alerts
- Dynamic list that updates automatically
- Proper icons for each source

---

## 🎯 How It Works

### Without API Keys
If you DON'T have FIRMS or WMATA keys:
- System logs a warning and skips those sources
- Dashboard shows only available sources (NWS, USGS EQ, NWIS)
- Everything else works normally!

### With API Keys
If you HAVE FIRMS and WMATA keys:
- System fetches fire detections and transit incidents
- Dashboard shows all 5 sources
- Complete emergency coverage!

---

## 🔍 Expected Behavior

### NASA FIRMS Alerts
**What you'll see:**
- Title: "Thermal Anomaly Detected (Brightness: XXXX°K)"
- Summary: Fire or thermal anomaly details
- Severity: Based on confidence (High/Nominal)
- Location: Latitude/Longitude
- Source Icon: 🔥 (fire icon)

### WMATA Alerts
**What you'll see:**
- Title: "Transit Incident — [Incident Type]"
- Summary: Description of the incident
- Severity: Based on incident type (delays, suspensions)
- Area: Affected metro lines
- Source Icon: 🚇 (train icon)

---

## 📊 Source Display Logic

The dashboard sidebar now shows:

**Before (static):**
```
Data Sources:
• NWS Weather Alerts
• USGS Earthquakes
• USGS NWIS (Rivers)
• NASA FIRMS (Fires)
• WMATA Transit
```

**After (dynamic):**
```
Active Data Sources:
• NWS Weather Alerts       ← Only if we have NWS alerts
• USGS Earthquakes         ← Only if we have earthquake data
• NASA FIRMS (Fires)       ← Only if we have fire detections
```

**Benefits:**
- ✅ No confusion about which sources are active
- ✅ Real-time indication of data availability
- ✅ Clean, accurate representation
- ✅ Automatically updates as alerts come in

---

## 🐛 Troubleshooting

### "No active sources" showing
**Cause:** No alerts in database yet
**Fix:** Run ingestion: `python -m app.services.ingest_nws`

### FIRMS/WMATA not appearing
**Cause 1:** No API key configured
**Fix:** Add keys to `backend/.env`

**Cause 2:** No incidents in area
**Fix:** Enable `TEST_MODE=true` for wider coverage

### "Connection error" in sources list
**Cause:** API server not running or not accessible
**Fix:** Check http://localhost:8000/api/health

---

## ✅ Verification Checklist

After running ingestion, verify:

- [ ] API responds: http://localhost:8000/api/alerts
- [ ] Dashboard loads: http://localhost:3000
- [ ] Source list shows active sources only
- [ ] Fire icon (🔥) appears if FIRMS data exists
- [ ] Train icon (🚇) appears if WMATA data exists
- [ ] Clicking alerts shows proper details

---

## 📈 Data Coverage

### TEST_MODE=true (recommended for testing)
- **NWS**: Virginia-wide weather alerts
- **USGS EQ**: Global earthquakes M4.5+
- **NWIS**: Potomac River gauges
- **FIRMS**: Virginia fire detections
- **WMATA**: All metro incidents

### TEST_MODE=false (production)
- **NWS**: Alexandria-specific
- **USGS EQ**: 10km radius from Alexandria
- **NWIS**: Local gauges
- **FIRMS**: Alexandria bbox only
- **WMATA**: All metro incidents (region-wide)

---

## 🚀 Continuous Monitoring

For 24/7 operation, run the scheduler:

```bash
cd backend
.\venv\Scripts\Activate.ps1
python -m app.services.ingest_scheduler
```

This will:
- Fetch from ALL 5 sources every 5 minutes
- Handle API key availability automatically
- Log all ingestion results
- Keep your dashboard updated!

---

## 📝 Summary

**New Files:**
- `backend/app/services/ingest_fires.py` - NASA FIRMS ingestion
- `backend/app/services/ingest_wmata.py` - WMATA ingestion

**Modified Files:**
- `backend/app/services/ingest_scheduler.py` - Added new sources
- `frontend/index.html` - Dynamic source display

**New Features:**
- 🔥 Fire detection via NASA FIRMS
- 🚇 Transit incidents via WMATA
- 📊 Dynamic source list on dashboard
- ✅ Automatic handling of missing API keys

**All done! Your system now supports 5 data sources with smart, dynamic display!** 🎉

