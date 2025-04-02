import json
import asyncio
from datetime import datetime
from app.services.knowledge_base import get_stats

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

async def main():
    # Get the stats
    stats = await get_stats()
    
    # Convert to dict and print with pretty formatting
    stats_dict = stats.dict()
    print(json.dumps(stats_dict, indent=2, cls=DateTimeEncoder))

if __name__ == "__main__":
    asyncio.run(main())