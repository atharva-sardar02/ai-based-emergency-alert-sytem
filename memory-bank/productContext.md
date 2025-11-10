# Product Context: Alexandria Emergency Alert System

## Why This Project Exists

Emergency management personnel need to monitor multiple disparate data sources to stay informed about potential threats to Alexandria. Manually checking NWS weather alerts, USGS earthquake data, river gauge readings, fire detection systems, and transit incidents is time-consuming and error-prone. Critical alerts can be missed or delayed.

This system solves the **consolidation problem** by bringing all emergency data into one unified interface with intelligent prioritization.

## Problems It Solves

### 1. Information Overload
- **Problem**: Too many alerts from too many sources
- **Solution**: AI-powered criticality classification (High/Medium/Low) helps prioritize what matters most
- **Enhancement**: Source filtering allows users to focus on specific data sources

### 2. Duplicate Alerts
- **Problem**: Same alert appears multiple times from different sources
- **Solution**: Deterministic natural key generation with database constraints prevents duplicates

### 3. Manual Triage
- **Problem**: Emergency managers must read every alert to determine relevance
- **Solution**: Automated classification with rationale provides quick context

### 4. Disconnected Systems
- **Problem**: Data sources have different formats, APIs, and update frequencies
- **Solution**: Unified normalization schema and consistent ingestion pipeline

### 5. Team Coordination
- **Problem**: No way to track which alerts have been acknowledged or acted upon
- **Solution**: User actions (acknowledge, irrelevant) with notes for team visibility

### 6. Source Visibility
- **Problem**: Hard to know which data sources are actively providing alerts
- **Solution**: Dynamic source list shows only active sources with actual data

## How It Should Work

### User Experience Flow

1. **Dashboard View** (Primary Interface)
   - User opens dashboard (http://localhost:3000)
   - Sees **source filter bar** at top with checkboxes for each active source
   - Can filter alerts by selecting specific sources
   - Sees list of alerts sorted by time (newest first, irrelevant at bottom)
   - Each alert card shows:
     - Title, summary, source
     - Criticality badge (High/Medium/Low with color coding)
     - Time ago display
     - Action buttons ("Know More", "Irrelevant")
   - Sidebar shows **only active sources** (sources with actual alerts)

2. **Source Filtering**
   - User clicks checkboxes to filter by source
   - Dashboard updates immediately to show only selected sources
   - "Clear" button resets all filters
   - Filter state persists during session

3. **Alert Details Modal**
   - Click "Know More" opens modal
   - Shows full alert information:
     - All normalized fields
     - AI classification rationale
     - Source URL and raw payload
     - Timestamps
   - Can acknowledge with optional note

4. **Alert Actions**
   - **Mark Irrelevant**: Moves alert to bottom of list (faded, 50% opacity), shows "Marked Irrelevant" badge
   - **Acknowledge**: Marks as handled, adds badge, stores note with timestamp
   - Actions persist in database and show in UI
   - Irrelevant alerts remain visible for reference

5. **Map View**
   - Click "Map View" button to see alerts on interactive map
   - Markers colored by criticality (Red=High, Orange=Medium, Yellow=Low)
   - Source-specific icons
   - Filtering by source and criticality
   - Auto-fit bounds to show all alerts

6. **Background Processing**
   - Ingestion runs every 5 minutes (all 5 sources automatically)
   - Classification worker continuously processes unclassified alerts
   - System auto-refreshes dashboard every 60 seconds

### System Behavior

**Ingestion Process:**
1. Scheduler triggers all 5 source-specific ingestion services in parallel
2. Each service fetches raw data from external API
3. Data normalized to common schema
4. Natural key generated (SHA256 of source + provider_id + timestamp)
5. Attempt insert into database (duplicates ignored via unique constraint)
6. Geographic coordinates extracted and stored (if available)
7. New alerts trigger classification

**Classification Process:**
1. Background worker polls for unclassified alerts
2. Attempts LLM classification via Ollama (using OLLAMA_BASE_URL from settings)
3. If LLM unavailable, uses rule-based fallback
4. Stores classification with rationale and model version
5. Frontend shows classification immediately

**Deduplication:**
- Database-level uniqueness on `natural_key` column
- Prevents same alert from being stored twice
- Handles clock skew and timezone differences
- Gracefully handles retries and re-ingestion

**Source Filtering:**
- Client-side filtering for instant response
- Filter options dynamically generated from active sources
- Multiple sources can be selected simultaneously
- Filter state cached in browser memory

## User Experience Goals

### For Emergency Managers
- **Quick Assessment**: See what needs attention immediately
- **Focused View**: Filter by source to focus on specific threat types
- **Confidence**: Know that critical items are highlighted
- **Efficiency**: Spend less time on irrelevant noise
- **Visibility**: Track team acknowledgments and notes
- **Source Awareness**: Know which data sources are active

### For Analysts
- **Context**: AI rationale explains why alert is High/Medium/Low
- **Provenance**: Access raw payload and source URLs for validation
- **History**: All alerts stored with full audit trail
- **Filtering**: Quickly isolate alerts from specific sources

### For Supervisors
- **Oversight**: View all alerts and team actions
- **Validation**: Check raw data before escalation
- **Coordination**: See acknowledgment notes
- **Source Monitoring**: Track which sources are providing data

## Design Principles

1. **Simplicity First**: MVP focuses on core functionality, avoids complexity
2. **Graceful Degradation**: Works without API keys, LLM fallbacks to rules
3. **Data Integrity**: Database constraints ensure no duplicates, referential integrity
4. **Transparency**: All classifications include rationale, raw payload available
5. **Extensibility**: Easy to add new data sources via base class pattern
6. **User Control**: Filtering and actions give users control over their view

## Key Interactions

### Critical Path: New Alert Flow
1. External source publishes new alert
2. Ingestion service fetches and normalizes
3. Natural key prevents duplicate
4. Alert stored in database with coordinates
5. Classification worker processes alert
6. Frontend polls API and displays new alert
7. Source filter options update if new source appears
8. User views, filters, acknowledges, or dismisses

### Error Handling
- Ingestion failures logged, retry on next cycle
- LLM unavailable falls back to rule-based classification
- Database errors logged, ingestion continues for other sources
- Frontend handles API errors gracefully
- Missing API keys gracefully skip optional sources

## Success Metrics (Future)

- Time to assess new alerts reduced from minutes to seconds
- Duplicate alerts eliminated
- Critical alerts never missed
- Team coordination improved via acknowledgments
- System uptime >99% during active hours
- User satisfaction with filtering and organization
