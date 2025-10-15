# API Keys Information

## Required API Keys

Your emergency alert system needs these API keys for full functionality:

---

## 1. NASA FIRMS (Fire/Heat Detection) ⭐ RECOMMENDED

**What it provides:**
- Real-time fire and thermal anomaly detection
- Global coverage with satellite imagery
- Essential for wildfire and fire emergency alerts

**How to get it:**
1. Visit: https://firms.modaps.eosdis.nasa.gov/api/area/
2. Click "Request API Key" or "Get Started"
3. Fill out the form:
   - Name
   - Email
   - Organization: City of Alexandria Emergency Management
   - Use Case: Emergency Alert System
4. You'll receive the key via email instantly (usually)

**Add to `.env`:**
```env
FIRMS_API_KEY=your_key_here
```

**Cost:** FREE ✅

---

## 2. WMATA (Washington Metro Transit)

**What it provides:**
- Metro rail incidents
- Bus alerts
- Service disruptions
- Important for Alexandria residents using DC metro

**How to get it:**
1. Visit: https://developer.wmata.com/
2. Click "Sign Up" (top right)
3. Create an account
4. Go to "Account" → "My Subscriptions"
5. Subscribe to "Default Tier" (free)
6. Get your "Primary Key"

**Add to `.env`:**
```env
WMATA_API_KEY=your_key_here
```

**Cost:** FREE ✅ (with rate limits)

---

## Sources That DON'T Need API Keys

These work out of the box:

### ✅ NWS (National Weather Service)
- Weather alerts, warnings, watches
- No API key required
- Public government data

### ✅ USGS Earthquakes
- Earthquake detection and monitoring
- No API key required
- Public USGS data

### ✅ USGS NWIS (River Gauges)
- River levels and flood monitoring
- No API key required
- Public USGS data

### ✅ NASA EONET (Wildfires - Fallback)
- Global wildfire events
- No API key required
- Used if FIRMS key not provided

---

## System Behavior Without Keys

Your system will work without API keys, but with limitations:

| Source | Without Key | With Key |
|--------|-------------|----------|
| **NWS** | ✅ Full access | ✅ Full access |
| **USGS Earthquakes** | ✅ Full access | ✅ Full access |
| **USGS NWIS** | ✅ Full access | ✅ Full access |
| **Fire Detection** | ⚠️ Limited (EONET only) | ✅ Full (FIRMS satellite data) |
| **WMATA Transit** | ❌ No transit alerts | ✅ Transit incident alerts |

---

## Priority Recommendation

### High Priority: Get FIRMS Key
- Takes 5 minutes
- Dramatically improves fire detection
- Essential for comprehensive emergency monitoring

### Medium Priority: Get WMATA Key
- Takes 5 minutes
- Useful for Alexandria residents
- Covers transit-related emergencies

---

## Example `.env` File With Keys

```env
# Database
DATABASE_URL=postgresql://eas_user:eas_password@localhost:5432/alexandria_eas

# API Keys
FIRMS_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6  # <- Your FIRMS key here
WMATA_API_KEY=1234567890abcdef1234567890abcdef  # <- Your WMATA key here

# LLM Configuration
MODEL_NAME=llama3.2:3b-instruct-q4
OLLAMA_BASE_URL=http://localhost:11434

# Application Settings
TEST_MODE=true
REFRESH_INTERVAL_SECONDS=300
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:3000
```

---

## After Adding Keys

1. Save the `.env` file
2. Restart the backend:
   ```powershell
   # Stop the server (Ctrl+C)
   # Then restart:
   uvicorn app.main:app --reload --port 8000
   ```
3. Run ingestion to fetch new data:
   ```powershell
   python -m app.services.ingest_scheduler
   ```

---

## Rate Limits

### FIRMS (NASA)
- Limit: 10,000 requests/day
- Your system: ~288 requests/day (every 5 min)
- **Status:** ✅ Well within limits

### WMATA
- Limit: 10,000 requests/day (default tier)
- Your system: ~288 requests/day
- **Status:** ✅ Well within limits

---

## Testing Keys Work

After adding keys, test each source:

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Test FIRMS (fire detection)
python -c "from app.settings import settings; print('FIRMS Key:', settings.FIRMS_API_KEY[:10] + '...' if settings.FIRMS_API_KEY else 'NOT SET')"

# Test WMATA
python -c "from app.settings import settings; print('WMATA Key:', settings.WMATA_API_KEY[:10] + '...' if settings.WMATA_API_KEY else 'NOT SET')"
```

Then run ingestion:
```powershell
python -m app.services.ingest_fires    # Should use FIRMS if key is set
python -m app.services.ingest_wmata     # Should fetch transit alerts
```

---

## Security Notes

- ⚠️ NEVER commit `.env` file to git (already in `.gitignore`)
- ⚠️ Don't share API keys publicly
- ✅ Keys are free for non-commercial use
- ✅ Rate limits are generous for this use case

---

## Support

- **FIRMS Support:** https://firms.modaps.eosdis.nasa.gov/contact/
- **WMATA Developer Support:** developer@wmata.com

---

Both keys are free and take less than 5 minutes each to obtain. Highly recommended for full system functionality!

