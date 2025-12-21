# 🚀 Bus Graph Cache Optimization

## Problem
The bus routing graph was being rebuilt from scratch every time the server started, taking 10-30 seconds. This was inefficient and slowed down development.

## Solution
Implemented **persistent caching** using Python's `pickle` module to save the built graph to disk and load it instantly on subsequent starts.

## How It Works

### First Server Start (Cold Start)
1. Loads CSV files (routes.csv, trips.csv, stops.csv)
2. Builds the bus graph using NetworkX (~10-30 seconds)
3. Builds route info and walking network
4. **Saves everything to `cache/bus_graph_cache.pkl`**
5. Server ready

**Time: ~10-30 seconds**

### Subsequent Server Starts (Warm Start)
1. Checks if `cache/bus_graph_cache.pkl` exists
2. Verifies cache is still valid (data files haven't changed)
3. **Loads pre-built graph from cache**
4. Server ready

**Time: <1 second** ⚡

## Cache Invalidation

The cache is automatically invalidated when:
- Any data file (routes.csv, trips.csv, stops.csv, walk_data.json) is modified
- The cache file is deleted or corrupted

## Manual Cache Management

### Clear Cache
If you update the data files and want to force a rebuild:

```bash
# Windows
python temp_server/clear_cache.py

# Linux/Mac
python3 temp_server/clear_cache.py
```

Or manually delete the cache:
```bash
rm -rf temp_server/cache/
```

### Check Cache Status
The server will print one of these messages on startup:

- `⚡ Loaded from cache in <1s!` - Cache hit (fast)
- `⚠️ Cache outdated (data files modified), rebuilding...` - Cache invalid
- `🔨 Building graph from scratch (this may take a while)...` - No cache

## Performance Improvement

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| First start | 10-30s | 10-30s | Same (must build) |
| Restart server | 10-30s | <1s | **10-30x faster** |
| Development cycle | Slow | Fast | Much better DX |

## Technical Details

### Cache File Location
```
temp_server/cache/bus_graph_cache.pkl
```

### Cached Objects
- `G_BUS` - NetworkX MultiDiGraph (bus network)
- `ROUTE_INFO` - Dictionary of route information
- `STOPS_DF` - Pandas DataFrame of bus stops
- `WALK_NODES` - Walking network nodes
- `WALK_GRAPH` - Walking network graph
- `data_mtime` - Timestamp for cache validation

### Cache Validation
The cache stores the modification time of all data files. On load, it compares:
- If data files are newer → Rebuild
- If cache is newer → Use cache

## Troubleshooting

### Cache Not Working
1. Check if `cache/` directory exists in `temp_server/`
2. Check file permissions
3. Clear cache and restart: `python clear_cache.py`

### Graph Seems Outdated
1. Clear the cache: `python clear_cache.py`
2. Restart the server

### Import Errors
Make sure all dependencies are installed:
```bash
pip install pandas networkx
```

## Notes

- Cache file is binary (pickle format) - not human readable
- Cache is platform-independent (works on Windows/Linux/Mac)
- Cache is added to `.gitignore` - won't be committed
- Safe to delete cache anytime - will rebuild automatically

## Future Improvements

Possible enhancements:
- Compress cache file (gzip) to reduce disk space
- Add cache versioning for breaking changes
- Implement partial cache updates
- Add cache warming on data file changes
