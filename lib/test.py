import asyncio
import websockets
import json

async def test_listener():
    url = "ws://localhost:8765"
    print(f"📡 Connecting to Jarvis Server at {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print("📱 Fake Flutter UI successfully connected!\n")
            print("🤖 Waiting for server broadcasts... Go ahead and press Ctrl+Shift+Space!")
            
            # Keep listening for incoming JSON messages forever
            async for message in websocket:
                data = json.loads(message)
                print(f"\n📥 RECEIVED FROM PYTHON:")
                print(f"   Status:  {data.get('status')}")
                print(f"   Message: {data.get('message')}")
                print("-" * 30)
                
    except ConnectionRefusedError:
        print("❌ Could not connect. Is your server script running in the other terminal?")

if __name__ == "__main__":
    asyncio.run(test_listener())