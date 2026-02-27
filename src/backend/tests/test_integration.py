import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src/backend"))

from app.services.ouo_bypass import OuoAutoBypass

def test_integration():
    print("Integration Test Started...")
    bot = OuoAutoBypass(debug_mode=True)
    
    test_urls = [
        "https://ouo.io/94jkLO",
        "https://ouo.press/cZNW9m"
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        result = bot.hedef_linki_bul(url)
        print(f"Result: {result}")
        
    print("\nIntegration Test Completed.")

if __name__ == "__main__":
    test_integration()
