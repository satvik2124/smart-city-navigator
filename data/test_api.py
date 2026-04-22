import httpx
import asyncio
import json

async def test():
    api_key = '142250f8a180492d9e9c6231ce055cdf'
    
    async with httpx.AsyncClient() as client:
        r = await client.get('https://api.geoapify.com/v1/geocode/search', 
            params={'text': 'Delhi', 'apiKey': api_key})
        data = r.json()
        features = data.get('features', [])
        if features:
            src = features[0]
            print(f'Keys in feature: {list(src.keys())[:10]}')
            # Check for lat/lon in different places
            lat = src.get('lat') or src.get('properties', {}).get('lat')
            lon = src.get('lon') or src.get('properties', {}).get('lon')
            print(f'Delhi lat={lat}, lon={lon}')
            
            # Check properties
            props = src.get('properties', {})
            print(f'Properties lat={props.get("lat")}, lon={props.get("lon")}')

asyncio.run(test())
