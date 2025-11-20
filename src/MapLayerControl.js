import React from 'react';
import { TileLayer, LayersControl, LayerGroup } from 'react-leaflet';
import './css/MapLayerControl.css';

const { BaseLayer } = LayersControl;

/**
 * MapLayerControl - Component để chuyển đổi giữa các loại bản đồ
 * Hỗ trợ: OpenStreetMap, Satellite, Terrain, Dark Mode
 */
function MapLayerControl() {
    console.log('MapLayerControl rendered');

    return (
        <LayersControl position="topright">
            {/* OpenStreetMap - Map thường */}
            <BaseLayer checked name="Bản đồ thường">
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
            </BaseLayer>

            {/* Satellite - Map vệ tinh */}
            <BaseLayer name="Vệ tinh">
                <TileLayer
                    attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                />
            </BaseLayer>

            {/* Satellite with Labels - Vệ tinh có nhãn */}
            <BaseLayer name="Vệ tinh + Nhãn">
                <LayerGroup>
                    {/* Satellite */}
                    <TileLayer
                        attribution='Tiles &copy; Esri &mdash; Source: Esri, USDA, USGS, GeoEye...'
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    />

                    {/* Labels (OSM road + place names) */}
                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors'
                        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                        opacity={0.35}   // độ trong suốt để overlay
                    />
                </LayerGroup>
            </BaseLayer>

            {/* Terrain - Bản đồ địa hình */}
            <BaseLayer name="Địa hình">
                <TileLayer
                    attribution='&copy; <a href="https://opentopomap.org">OpenTopoMap</a> &mdash; Map data &copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                />
            </BaseLayer>

            {/* Dark Mode - Bản đồ tối */}
            <BaseLayer name="Chế độ tối">
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />
            </BaseLayer>

            {/* Light Mode - Bản đồ sáng (minimal) */}
            <BaseLayer name="Chế độ sáng">
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />
            </BaseLayer>
        </LayersControl>
    );
}

export default MapLayerControl;
