import numpy as np
import pandas as pd
from pykrige.ok import OrdinaryKriging
from typing import List, Dict, Any
from app.core.supabase import get_supabase_admin
import shapely.wkb
from shapely.geometry import mapping
import json

class SpatialService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    async def generate_village_mapping(self, district: str = "Krishna"):
        """
        Generates village-level groundwater mapping using Kriging interpolation.
        1. Fetch latest piezometer readings with coordinates.
        2. Fetch village centroids.
        3. Perform Ordinary Kriging.
        4. Update villages table with estimated levels.
        """
        # 1. Fetch data
        query = self.supabase.table("piezometers").select(
            "geom, readings(water_level_mbgl)"
        ).eq("is_active", True).order("reading_date.desc", table="readings").limit(1, table="readings")
        
        response = query.execute()
        if not response.data:
            return None
            
        points = []
        values = []
        for item in response.data:
            if item.get("readings") and len(item["readings"]) > 0:
                # Extract coordinates from GeoJSON point
                coords = item["geom"]["coordinates"]
                points.append(coords)
                values.append(item["readings"][0]["water_level_mbgl"])
        
        if len(points) < 3: # Need at least 3 points for Kriging
            return {"error": "Insufficient data points"}

        points = np.array(points)
        values = np.array(values)

        # 2. Fetch Village Centroids
        villages_resp = self.supabase.table("villages").select("id, centroid").eq("district", district).execute()
        if not villages_resp.data:
            return {"error": "No villages found"}

        v_ids = []
        v_coords = []
        for v in villages_resp.data:
            if v["centroid"]:
                v_ids.append(v["id"])
                v_coords.append(v["centroid"]["coordinates"])

        v_coords = np.array(v_coords)

        # 3. Perform Ordinary Kriging
        OK = OrdinaryKriging(
            points[:, 0], points[:, 1], values,
            variogram_model='linear',
            verbose=False, enable_plotting=False
        )
        
        # Estimate values at village centroids
        z, ss = OK.execute('points', v_coords[:, 0], v_coords[:, 1])

        # 4. Prepare updates (This could be a bulk update or a new table for heatmaps)
        # For PoC, we update the villages table average_groundwater_level ( need to add this col or use a separate table)
        # We'll return the results for now
        results = []
        for i, v_id in enumerate(v_ids):
            results.append({
                "village_id": v_id,
                "estimated_level": float(z[i]),
                "variance": float(ss[i])
            })
            
        return results
    
    async def get_soil_at_location(self, lat: float, lon: float):
        """
        Get soil type at a specific coordinate using spatial intersection
        """
        try:
            # Use PostGIS ST_Contains to find soil polygon containing the point
            result = self.supabase.rpc(
                'get_soil_at_point',
                {'lat': lat, 'lon': lon}
            ).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            # Fallback: Query with JSONB if RPC not available
            # This is less efficient but works
            return {"message": "Soil data lookup requires PostGIS RPC function"}
        except Exception as e:
            return {"error": str(e), "message": "Spatial query failed"}
    
    async def get_elevation_at_location(self, lat: float, lon: float, radius_km: float = 1.0):
        """
        Get elevation at a specific coordinate
        Uses nearest neighbor search within radius
        """
        try:
            # Find nearest elevation point within radius
            result = self.supabase.rpc(
                'get_elevation_near_point',
                {'lat': lat, 'lon': lon, 'radius_km': radius_km}
            ).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return {"message": "No elevation data found within radius", "elevation_m": None}
        except Exception as e:
            return {"error": str(e), "message": "Elevation query failed"}
    
    async def get_model_zones(self, district: str = "Krishna"):
        """
        Get all groundwater model zones for a district
        """
        try:
            result = self.supabase.table("model_zones").select("*").eq("district", district).execute()
            return result.data if result.data else []
        except Exception as e:
            return {"error": str(e)}
    
    async def get_mit_zones(self, district: str = "Krishna", priority: int = None):
        """
        Get MIT (monitoring/intervention) zones, optionally filtered by priority
        """
        try:
            query = self.supabase.table("mit_zones").select("*").eq("district", district)
            
            if priority:
                query = query.eq("priority_level", priority)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            return {"error": str(e)}

    async def get_aquifers(self):
        """
        Get all aquifer zones with GeoJSON geometry
        """
        try:
            # Fetch all aquifers
            result = self.supabase.table("aquifers").select("*").execute()
            data = result.data if result.data else []
            return self._process_geometry(data, 'boundary')
        except Exception as e:
            print(f"Error fetching aquifers: {e}")
            return {"error": str(e)}

    async def get_bore_wells(self, limit: int = 1000):
        """
        Get bore wells (limited count for performance)
        """
        try:
            # Fetch bore wells
            result = self.supabase.table("bore_wells").select("*").limit(limit).execute()
            data = result.data if result.data else []
            return self._process_geometry(data, 'geom')
        except Exception as e:
            print(f"Error fetching bore wells: {e}")
            return {"error": str(e)}
            
    async def get_land_use_zones(self):
        """
        Get all Land Use / Land Cover zones
        """
        try:
            # Fetch LULC zones
            result = self.supabase.table("land_use_zones").select("*").execute()
            data = result.data if result.data else []
            return self._process_geometry(data, 'geom')
        except Exception as e:
            print(f"Error fetching LULC: {e}")
            return {"error": str(e)}

    async def get_piezometers(self):
        """
        Get all Piezometers (monitoring stations)
        """
        try:
            # Fetch Piezometers
            result = self.supabase.table("piezometers").select("*").execute()
            data = result.data if result.data else []
            return self._process_geometry(data, 'geom')
        except Exception as e:
            print(f"Error fetching piezometers: {e}")
            return {"error": str(e)}

    async def get_piezometer_readings(self, piezometer_id: str):
        """
        Get all water level readings for a specific piezometer
        """
        try:
            result = self.supabase.table("readings")\
                .select("reading_date, water_level_mbgl")\
                .eq("piezometer_id", piezometer_id)\
                .order("reading_date", desc=False)\
                .execute()
            
            data = result.data if result.data else []
            return data
        except Exception as e:
            print(f"Error fetching piezometer readings: {e}")
            return {"error": str(e)}

    def _process_geometry(self, data: List[Dict], geom_col: str):
        """
        Helper to convert WKB/WKT/GeoJSON to Python Dict GeoJSON
        """
        processed_data = []
        import shapely.wkt
        
        for item in data:
            if item.get(geom_col):
                try:
                    raw_geom = item[geom_col]
                    geom = None
                    
                    # Case 1: Already GeoJSON (dict)
                    if isinstance(raw_geom, dict):
                        item['geometry'] = raw_geom
                        processed_data.append(item)
                        continue

                    # Case 2: String (WKT or Hex WKB)
                    if isinstance(raw_geom, str):
                        clean_str = raw_geom.strip()
                        # Check for Hex (WKB)
                        is_hex = all(c in '0123456789ABCDEFabcdef' for c in clean_str[:10])
                        
                        if is_hex and len(clean_str) > 10:
                            try:
                                geom = shapely.wkb.loads(bytes.fromhex(clean_str))
                            except:
                                geom = shapely.wkt.loads(clean_str)
                        else:
                            geom = shapely.wkt.loads(clean_str)

                    if geom:
                        item['geometry'] = mapping(geom)
                        del item[geom_col]
                        processed_data.append(item)
                        
                except Exception as e:
                    # Skip invalid geometry items
                    continue
        return processed_data
    
    async def get_village_spatial_context(self, village_id: str):
        """
        Get comprehensive spatial context for a village including:
        - Soil types within village boundary
        - Average elevation
        - Model zone
        - MIT zone
        """
        try:
            # Get village info
            village = self.supabase.table("villages").select("*").eq("id", village_id).execute()
            
            if not village.data or len(village.data) == 0:
                return {"error": "Village not found"}
            
            v = village.data[0]
            
            # Get centroid coordinates (optional, for reference)
            if v.get("centroid"):
                coords = v["centroid"]["coordinates"] if isinstance(v["centroid"], dict) else None
                # lat, lon = coords[1], coords[0] if coords else (None, None)
                    
            # Try to get synthesized data from JSONB blocks first
            soil = v.get("soil_profile")
            if not soil or soil.get("soil_name") == "N/A":
                # Fallback to direct flat columns if JSONB is missing
                soil = {
                    "soil_name": v.get("soil_type") or "Unknown",
                    "texture": v.get("soil_texture") or "Mixed",
                    "drainage": v.get("soil_drainage") or "Moderate",
                    "message": "Direct column fallback"
                }
            
            elevation = v.get("elevation_data")
            if not elevation or not elevation.get("elevation_m"):
                elevation = {
                    "elevation_m": v.get("elevation_m") or 0,
                    "message": "Direct column fallback"
                }

            return {
                "village": v,
                "soil": soil,
                "elevation": elevation
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_district_boundary(self, district_name: str):
        """
        Get district boundary GeoJSON
        """
        try:
            result = self.supabase.table("districts").select("*").eq("name", district_name).execute()
            data = result.data if result.data else []
            processed = self._process_geometry(data, 'boundary')
            return processed[0] if processed else None
        except Exception as e:
            print(f"Error fetching district boundary: {e}")
            return None

    async def get_ap_districts(self):
        """
        Read and return the Andhra Pradesh districts GeoJSON data from local file
        """
        try:
            import os
            # Use absolute path to the geojson file
            file_path = r"d:\Smart Jal\backend\database\andhra-pradesh.geojson"
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return {"error": "GeoJSON file not found"}
        except Exception as e:
            print(f"Error reading AP districts GeoJSON: {e}")
            return {"error": str(e)}

spatial_service = SpatialService()
