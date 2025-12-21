# 🔧 Bus API Troubleshooting Guide

## ✅ Fixed Issues

### Issue: API returns 503 "Bus routing module not available"

**Root Cause:**
- `BUS_ROUTING_AVAILABLE` was set to `True` on import
- But data was not loaded until `if __name__ == "__main__"`
- When Flask reloader runs, data loading code might not execute

**Solution:**
Load data immediately after successful import:

```python
# Import bus routing modules
BUS_ROUTING_AVAILABLE = False
try:
    import graph_cache
    from Bus_Routing_Module import a_star, draw_map, nearby_stops, make_heuristic
    
    # Load data immediately
    graph_cache.load_all_data()
    BUS_ROUTING_AVAILABLE = True
    print("✅ Bus routing ready!")
except Exception as e:
    print(f"❌ Failed: {e}")
```

## 🧪 Testing

### 1. Test Module Import
```bash
cd temp_server
python -c "from API import BUS_ROUTING_AVAILABLE; print('Available:', BUS_ROUTING_AVAILABLE)"
```

Expected output:
```
✅ Bus routing modules loaded successfully
🚌 Loading bus routing data...
✅ Loaded 127 routes
✅ Loaded 5184 trips
✅ Loaded 4343 stops
✅ Bus routing ready!
Available: True
```

### 2. Test API Endpoint
```bash
python test_bus_api.py
```

Or use curl:
```bash
curl "http://localhost:5000/api/bus/route?start_lat=10.762679&start_lng=106.682586&end_lat=10.779509&end_lng=106.699328&max_walk=300"
```

### 3. Test from Frontend
Open browser console and run:
```javascript
fetch('http://localhost:5000/api/bus/route?start_lat=10.762679&start_lng=106.682586&end_lat=10.779509&end_lng=106.699328&max_walk=300')
  .then(r => r.json())
  .then(d => console.log(d))
```

## 📋 Checklist

Before running the server, ensure:

- [ ] All CSV files exist in `temp_server/`:
  - `routes.csv`
  - `stops.csv`
  - `trips.csv`

- [ ] All JSON files exist:
  - `car_data.json`
  - `walk_data.json`

- [ ] Python modules installed:
  ```bash
  pip install flask flask-cors pandas networkx folium numpy
  ```

- [ ] Working directory is `temp_server/`:
  ```bash
  cd temp_server
  python API.py
  ```

## 🐛 Common Errors

### Error: "No bus stop near start location"
**Cause:** Start location too far from any bus stop
**Solution:** Increase `max_walk` parameter (default 300m, try 500-1000m)

### Error: "No route found"
**Cause:** No bus route connects the two locations
**Solution:** Try different locations or check if they're in the same city

### Error: FileNotFoundError
**Cause:** CSV/JSON files not found
**Solution:** 
```bash
# Check files exist
ls routes.csv stops.csv trips.csv car_data.json walk_data.json

# Copy from busmapapi if needed
cp ../busmapapi/*.csv .
cp ../busmapapi/*.json .
```

### Error: Module import failed
**Cause:** Missing Python dependencies
**Solution:**
```bash
pip install pandas networkx folium numpy overpy geopy
```

## 📊 Performance

Expected response times:
- First request: 15-30 seconds (includes road routing)
- Subsequent requests: 10-20 seconds
- Simple routes: 5-10 seconds

If slower:
- Check CPU usage
- Check if OSM data is loading properly
- Consider using optimized version (Goong Maps)

## 🔍 Debug Mode

Enable detailed logging:
```python
# In API.py, add at the top
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check server logs for:
- `🚌 Bus routing from...` - Request received
- `✅ Bus route calculated...` - Success
- Any error messages

## 📞 Support

If issues persist:
1. Check server logs
2. Test with `test_bus_api.py`
3. Verify all files are present
4. Check Python version (3.8+)
5. Ensure port 5000 is not in use
