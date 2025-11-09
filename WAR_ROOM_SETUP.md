# Cerberus War Room - Quick Setup Guide

## What is the War Room?

The War Room transforms your terminal-based Cerberus demo into a **live, visual, event-driven dashboard** that judges can see and understand immediately. No more staring at terminal logs - watch the active defense system come to life.

## What You Built

### ✅ Dashboard Frontend (React + Next.js)
- `/dashboard/` - Complete Next.js application
- Real-time WebSocket connection for live events
- Visual components:
  - **ThreatMap**: Canvas-based world map showing green (normal) and red (attack) traffic
  - **EventCard**: Sliding threat notifications
  - **RoutingVisualizer**: Animation showing attacker being rerouted to honeypot
  - **LabyrinthTerminal**: Live stream of attacker actions
  - **SentinelPanel**: AI analysis with profiling, simulation, and rule generation
  - **MetricsBar**: Real-time stats (attacks detected, blocked, rules generated)

### ✅ Component Architecture
- `/dashboard/src/components/` - All UI components
- `/dashboard/src/hooks/useWarRoom.ts` - WebSocket state management
- `/dashboard/tailwind.config.js` - Custom Cerberus theme
- `/dashboard/app/page.tsx` - Main War Room interface

### 📋 What's Missing (Next Steps)

1. **Install dependencies**:
   ```bash
   cd dashboard
   npm install
   ```

2. **Create remaining components** (stubs exist in spec):
   - `src/components/RoutingVisualizer.tsx`
   - `src/components/LabyrinthTerminal.tsx`
   - `src/components/SentinelPanel.tsx`
   - `src/components/MetricsBar.tsx`

3. **Create WebSocket server**:
   ```bash
   mkdir war-room-server
   cd war-room-server
   npm init -y
   npm install express socket.io cors
   # Create server.js (see WAR_ROOM_SPEC.md)
   ```

4. **Integrate with Cerberus services**:
   Add WebSocket event emission to:
   - `gatekeeper/api/main.py` - emit threat events
   - `switch/api/main.py` - emit routing updates
   - `labyrinth/app/main.py` - emit attacker activity
   - `sentinel/api/main.py` - emit AI analysis

## Quick Start (When Ready)

```bash
# Terminal 1: Start Cerberus services
docker compose up -d

# Terminal 2: Start War Room WebSocket server
cd war-room-server
node server.js
# Listening on port 8004

# Terminal 3: Start dashboard
cd dashboard
npm run dev
# Dashboard at http://localhost:3002

# Terminal 4: Run demo (events stream to dashboard)
./scripts/demo.sh
```

## The Demo Flow (What Judges See)

### Before: Terminal Demo
```
$ curl -X POST http://localhost:8000/api/v1/inspect ...
{"action":"tag_poi","scores":{"combined":62.21},...}
```
❌ Hard to understand, not visual

### After: War Room
1. **Map lights up** with hundreds of green lines (normal traffic)
2. **Red pulsing line appears** - attack detected!
3. **Event card slides in**:
   ```
   THREAT DETECTED
   SQL Injection - Score: 62.21
   Action: TAG_POI
   ```
4. **Routing animation** shows attacker being disconnected from Production and rerouted to Labyrinth
5. **Labyrinth terminal** streams live attacker behavior
6. **Sentinel AI panel** shows intelligent analysis and rule generation
7. **Final verification** - subsequent attacks blocked, shown visually

✅ Judges understand immediately, visual proof of safeguarding

## Why This Fixes the "No Visuals" Problem

**Current State**: Cerberus works perfectly but looks like terminal output. Judges have to imagine the defense happening.

**With War Room**: Every step of the active defense is visualized in real-time:
- Detection → Red line appears on map
- Deception → Animation shows routing to honeypot
- Analysis → AI panel fills with profiling data
- Response → Rule generation shown with confidence meter
- Verification → Blocked attacks flash and disappear

## Advanced Feature: Adaptive Labyrinth

The War Room enables a feedback loop between Sentinel and Labyrinth:

### Low-Skill Attacker (Script Kiddie)
```
Sentinel: "Sophistication 2/10 - keep them busy"
↓
Labyrinth: Intentionally leaks fake config.bak
↓
War Room shows: "> Downloading fake credentials..."
↓
Result: Attacker wastes 20 minutes
```

### High-Skill Attacker (APT)
```
Sentinel: "Sophistication 9/10 - we need their tools"
↓
Labyrinth: Presents fake S3 bucket endpoint
↓
War Room shows: "> Attempting exfiltration with custom tool"
↓
Result: Captured zero-day malware in sandbox
```

## Files Created

```
dashboard/
├── package.json                    # Dependencies (Next.js, React, Socket.IO, etc.)
├── tailwind.config.js              # Cerberus theme (green primary, red danger)
├── app/
│   └── page.tsx                    # Main War Room interface
├── src/
│   ├── components/
│   │   ├── ThreatMap.tsx          # ✅ World map with traffic visualization
│   │   ├── EventCard.tsx          # ✅ Sliding threat notifications
│   │   ├── RoutingVisualizer.tsx  # 📋 TODO: Routing animation
│   │   ├── LabyrinthTerminal.tsx  # 📋 TODO: Live attacker log
│   │   ├── SentinelPanel.tsx      # 📋 TODO: AI analysis display
│   │   └── MetricsBar.tsx         # 📋 TODO: Real-time stats
│   └── hooks/
│       └── useWarRoom.ts           # ✅ WebSocket state management
└── WAR_ROOM_SPEC.md                # 📋 Complete implementation guide

war-room-server/                    # 📋 TODO: WebSocket server
└── server.js                       # Handles events from all services
```

## Next Actions

1. **Install dashboard dependencies**:
   ```bash
   cd dashboard && npm install
   ```

2. **Create the 4 missing components** using templates in `WAR_ROOM_SPEC.md`

3. **Set up WebSocket server**:
   ```bash
   mkdir war-room-server && cd war-room-server
   npm init -y
   npm install express socket.io cors body-parser
   # Copy server.js from spec
   ```

4. **Add event emission to services** (Python socketio-client):
   ```bash
   pip install python-socketio
   ```
   Then add emissions to Gatekeeper, Switch, Labyrinth, Sentinel APIs

5. **Test the full flow**:
   ```bash
   docker compose up -d
   cd war-room-server && node server.js &
   cd dashboard && npm run dev &
   ./scripts/demo.sh
   # Open http://localhost:3002
   ```

## Success Criteria

The War Room is working when:
- ✅ Dashboard loads at `http://localhost:3002`
- ✅ Green traffic lines flow to server on map
- ✅ Running `demo.sh` triggers event cards to appear
- ✅ Routing visualization shows attacker being rerouted
- ✅ Labyrinth terminal streams attacker actions
- ✅ Sentinel panel shows AI analysis
- ✅ Metrics update in real-time
- ✅ Judges can understand the entire flow without looking at terminal

## Documentation

- **Full Spec**: `/dashboard/WAR_ROOM_SPEC.md`
- **Component Details**: See individual `.tsx` files in `/dashboard/src/components/`
- **WebSocket Events**: Documented in `WAR_ROOM_SPEC.md` under "WebSocket Event Schema"
- **Integration Guide**: See "Integration Points" section in spec

## Support

If you get stuck:
1. Check `WAR_ROOM_SPEC.md` for detailed implementation guides
2. Verify all services are running (`docker compose ps`)
3. Check WebSocket server logs (`war-room-server` terminal)
4. Confirm dashboard is connected (green "LIVE" indicator)
5. Test with `curl` commands before running full demo
