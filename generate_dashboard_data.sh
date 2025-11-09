#!/bin/bash

echo "🚀 Generating comprehensive dashboard data for Cerberus..."
echo ""

# SQL Injection Attacks (15 requests)
echo "1️⃣  SQL Injection Attacks..."
for i in {1..15}; do
  curl -s -X POST http://localhost:8000/api/v1/inspect \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"GET\",\"url\":\"http://test.com/api/users?id=$i' UNION SELECT password FROM users--\",\"headers\":{\"User-Agent\":\"sqlmap/1.0\"},\"body\":\"\",\"query_params\":{},\"client_ip\":\"192.168.1.$((i % 255))\",\"session_id\":\"sql-attack-$i\"}" > /dev/null
  echo "  ✓ SQL attack $i"
  sleep 0.4
done

# XSS Attacks (10 requests)
echo ""
echo "2️⃣  XSS Attacks..."
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/v1/inspect \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"POST\",\"url\":\"http://test.com/comment\",\"headers\":{\"User-Agent\":\"Chrome/90.0\"},\"body\":\"<script>alert('XSS-$i')</script>\",\"query_params\":{},\"client_ip\":\"203.0.113.$((i % 255))\",\"session_id\":\"xss-attack-$i\"}" > /dev/null
  echo "  ✓ XSS attack $i"
  sleep 0.4
done

# Normal Traffic (25 requests)
echo ""
echo "3️⃣  Normal Traffic..."
for i in {1..25}; do
  curl -s -X POST http://localhost:8000/api/v1/inspect \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"GET\",\"url\":\"http://test.com/api/users?page=$i\",\"headers\":{\"User-Agent\":\"Mozilla/5.0\"},\"body\":\"\",\"query_params\":{},\"client_ip\":\"10.0.0.$((i % 255))\",\"session_id\":\"normal-$i\"}" > /dev/null
  echo "  ✓ Normal request $i"
  sleep 0.2
done

# Honeypot Interactions (15 requests)
echo ""
echo "4️⃣  Honeypot Interactions..."
for i in {1..15}; do
  curl -s http://localhost:8002/api/v1/users > /dev/null
  curl -s http://localhost:8002/admin/config > /dev/null
  curl -s http://localhost:8002/.env > /dev/null
  echo "  ✓ Honeypot interaction $i"
  sleep 0.5
done

# Sentinel Simulations (5 requests)
echo ""
echo "5️⃣  Sentinel Simulations..."
for i in {1..5}; do
  curl -s -X POST http://localhost:8003/api/v1/sentinel/simulate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: sentinel-dev-key-change-me" \
    -d '{"payload":{"type":"sql_injection","value":"1 OR 1=1","confidence":0.9},"shadow_app_ref":"main","metadata":{}}' > /dev/null
  echo "  ✓ Simulation $i"
  sleep 1
done

echo ""
echo "✅ Dashboard data generation complete!"
echo ""
echo "📊 Summary:"
echo "  - SQL Injection attacks: 15"
echo "  - XSS attacks: 10"
echo "  - Normal traffic: 25"
echo "  - Honeypot interactions: 45 (15×3 endpoints)"
echo "  - Sentinel simulations: 5"
echo ""
echo "🌐 Open Grafana dashboard: http://localhost:3001/d/cerberus-overview/cerberus-overview"
echo "   Login: admin / admin"
echo ""
echo "✨ The dashboard should now show live data!"
