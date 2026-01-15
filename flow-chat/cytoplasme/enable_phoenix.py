#!/usr/bin/env python3
"""
Enable Temporal Elasticity Phoenix in cytoplasme
"""
try:
    from phoenix_adaptive import phoenix
    
    # Start adaptive phoenix
    phoenix.start()
    
    print("🔥 PHOENIX ENABLED: Temporal Elasticity Mode")
    print(f"   Current stress: {phoenix.calculate_stress():.2f}")
    print(f"   Next check in: {phoenix.calculate_phoenix_timing() or 'PAUSED (flow state)'}")
    
except ImportError as e:
    print(f"❌ Phoenix import failed: {e}")
except Exception as e:
    print(f"❌ Phoenix activation failed: {e}")