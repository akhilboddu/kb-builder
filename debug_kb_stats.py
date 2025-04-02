import json
import asyncio
from datetime import datetime
from app.services.knowledge_base import get_stats
from app.db.vector_store import count_items_by_metadata, count_total_documents

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

async def main():
    # Debug count_items_by_metadata function for different keys
    print("=== DEBUG COUNTS ===")
    
    # Test type counts
    pdf_documents = await count_items_by_metadata(filter_key="type", filter_value="pdf")
    web_documents = await count_items_by_metadata(filter_key="type", filter_value="web")
    print(f"PDF documents: {pdf_documents}")
    print(f"Web documents: {web_documents}")
    
    # Test source counts
    sources = await count_items_by_metadata(filter_key="source")
    print(f"Sources: {json.dumps(sources, indent=2, cls=DateTimeEncoder)}")
    
    # Test category counts
    categories = await count_items_by_metadata(filter_key="category")
    print(f"Categories: {json.dumps(categories, indent=2, cls=DateTimeEncoder)}")
    
    # Test document counts
    total_docs = await count_total_documents()
    print(f"Total documents (count_total_documents): {total_docs}")
    
    # Test page counts
    total_pages_data = await count_items_by_metadata(filter_key="page_number", count_unique=True)
    print(f"Page numbers: {json.dumps(total_pages_data, indent=2, cls=DateTimeEncoder)}")
    
    # Get the stats and print
    print("\n=== FINAL STATS ===")
    stats = await get_stats()
    stats_dict = stats.dict()
    print(json.dumps(stats_dict, indent=2, cls=DateTimeEncoder))

if __name__ == "__main__":
    asyncio.run(main())