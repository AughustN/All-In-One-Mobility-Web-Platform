# ⚡ Quick Cache Guide

## What Changed?

Bus graph loading is now **10-30x faster** after the first run!

## How to Use

### Normal Usage (No Action Needed)
Just start the server as usual:
```bash
cd temp_server
python API.py
```

**First time:** Takes 10-30 seconds (builds graph + saves cache)
**Next times:** Takes <1 second (loads from cache) ⚡

### When You Update Data Files

If you modify `routes.csv`, `trips.csv`, `stops.csv`, or `walk_data.json`:

**Option 1: Automatic (Recommended)**
- Just restart the server
- Cache will detect changes and rebuild automatically

**Option 2: Manual Clear**
```bash
python clear_cache.py
python API.py
```

### Test Cache Performance
```bash
python test_cache.py
```

Run it twice to see the difference:
- First run: ~10-30 seconds
- Second run: <1 second

## Cache Location
```
temp_server/cache/bus_graph_cache.pkl
```

Safe to delete anytime - will rebuild automatically.

## Troubleshooting

**Problem:** Server still slow after restart
**Solution:** 
```bash
python clear_cache.py
python API.py
```

**Problem:** "Cache outdated" message every time
**Solution:** Your data files are being modified. This is normal if you're actively editing them.

**Problem:** Import errors
**Solution:** Make sure you're in the temp_server directory:
```bash
cd temp_server
python API.py
```

## Benefits

✅ Faster development (instant server restarts)
✅ Faster testing (no waiting for graph rebuild)
✅ Automatic cache invalidation (always up-to-date)
✅ No configuration needed (works out of the box)
