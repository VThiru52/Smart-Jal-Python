import asyncio
import os
import sys

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.recharge_service import recharge_service

async def main():
    print("🚀 Starting Recharge Service Diagnostic...")
    try:
        results = await recharge_service.calculate_recharge_priorities("Krishna")
        if isinstance(results, dict) and "error" in results:
            print(f"❌ Service returned error dict: {results['error']}")
        else:
            print(f"✅ Success! Found {len(results)} recommendations.")
            print(f"Sample: {results[0] if results else 'None'}")
    except Exception as e:
        import traceback
        print("💥 CRITICAL CRASH in Diagnostic:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
