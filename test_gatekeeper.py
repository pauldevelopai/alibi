"""
Test Vision Gatekeeper Pipeline

Demonstrates the vision-first approach:
1. Vision detections FIRST
2. Rule-based scoring
3. Gate decision (eligible/not eligible)
4. LLM OPTIONALLY enriches AFTER

No LLM required for incident creation!
"""

import cv2
import sys
from pathlib import Path

# Add alibi to path
sys.path.insert(0, str(Path(__file__).parent))

from alibi.vision.gatekeeper import VisionGatekeeper, GatekeeperPolicy
from alibi.schema.incidents import VisionIncident

def test_gatekeeper_on_image(image_path: str):
    """
    Test the gatekeeper on a single image.
    
    This demonstrates:
    1. YOLO detection (vision first)
    2. Zone-aware scoring (rule-based)
    3. Eligibility gate (policy-based)
    4. Structured incident creation (LLM-free)
    """
    print("\n" + "="*70)
    print("VISION-FIRST GATEKEEPER TEST")
    print("="*70)
    
    # Load image
    print(f"\n1. Loading image: {image_path}")
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"   ❌ Failed to load: {image_path}")
        return False
    print(f"   ✅ Loaded: {frame.shape[1]}x{frame.shape[0]} pixels")
    
    # Initialize gatekeeper
    print("\n2. Initializing Vision Gatekeeper")
    print("   • Model: YOLOv8n (nano, fast)")
    print("   • Policy: default security thresholds")
    
    policy = GatekeeperPolicy(
        min_vision_conf=0.4,      # Lower for testing
        min_rule_conf=0.5,
        min_combined_conf=0.45
    )
    
    gatekeeper = VisionGatekeeper(model_path="yolov8n.pt", policy=policy)
    print("   ✅ Gatekeeper ready")
    
    # Process frame (NO LLM YET!)
    print("\n3. Running Vision Detection (NO LLM)")
    result = gatekeeper.process_frame(frame, zones_config=None)
    
    # Show detections
    print(f"\n   📊 Detections: {len(result['detections'])}")
    for det in result['detections']:
        print(f"      • {det.class_name}: {det.confidence:.2f}")
    
    # Show scores
    score = result['score']
    print(f"\n   📈 Scores:")
    print(f"      • Vision: {score.vision_conf:.2f}")
    print(f"      • Rules: {score.rule_conf:.2f}")
    print(f"      • Combined: {score.combined_conf:.2f}")
    print(f"      • Reason: {score.reason}")
    
    # Show gate decision
    print(f"\n   🚦 Gate Decision: {'✅ PASS' if result['eligible'] else '❌ REJECT'}")
    print(f"      • {result['reason']}")
    
    # Create incident (if eligible)
    if result['eligible']:
        print("\n4. Creating Vision Incident (LLM-FREE)")
        
        incident = VisionIncident.from_gatekeeper_result(
            camera_id="test_camera",
            result=result,
            evidence_frames=[image_path]
        )
        
        print(f"   ✅ Incident created:")
        print(f"      • ID: {incident.id}")
        print(f"      • Category: {incident.category.value}")
        print(f"      • Training eligible: {incident.flags.training_eligible}")
        print(f"      • LLM required: {not incident.flags.llm_optional}")
        
        # Show what would go into training
        if incident.flags.training_eligible:
            print(f"\n   📚 Training Data (NO LLM CAPTION NEEDED):")
            print(f"      • Classes: {', '.join(incident.detections.classes)}")
            print(f"      • Counts: {incident.detections.counts}")
            print(f"      • Confidence: {incident.detections.avg_confidence:.2f}")
            print(f"      • Security relevant: {incident.detections.security_relevant}")
            
            print(f"\n   ✅ This would be stored as STRUCTURED training data")
            print(f"      (NOT as an LLM caption that might be wrong!)")
        
        return True
    else:
        print("\n4. Incident REJECTED by gate")
        print(f"   ❌ This would be stored as BASELINE/NOISE, not training")
        print(f"   ❌ No LLM wasted on non-relevant footage")
        
        return False


def test_with_llm_enrichment(image_path: str):
    """
    Optional: Show how LLM enrichment works AFTER the gate.
    
    THE KEY: Incident exists WITHOUT LLM.
    LLM just adds optional description.
    """
    print("\n" + "="*70)
    print("OPTIONAL: LLM ENRICHMENT (AFTER GATE)")
    print("="*70)
    
    # First, run gate
    frame = cv2.imread(image_path)
    gatekeeper = VisionGatekeeper(model_path="yolov8n.pt")
    result = gatekeeper.process_frame(frame)
    
    if not result['eligible']:
        print("\n❌ Gate rejected. NO LLM called (saved money + time)")
        return
    
    # Gate passed, create incident
    incident = VisionIncident.from_gatekeeper_result(
        camera_id="test_camera",
        result=result,
        evidence_frames=[image_path]
    )
    
    print(f"\n✅ Incident exists (ID: {incident.id})")
    print(f"   • Category: {incident.category.value}")
    print(f"   • Detections: {', '.join(incident.detections.classes)}")
    
    # NOW we can optionally call LLM for enrichment
    print(f"\n📝 Optional LLM Enrichment:")
    print(f"   • Incident already exists with structured data")
    print(f"   • LLM could add natural language description")
    print(f"   • But if LLM fails/refuses, incident still valid!")
    
    try:
        # This is where you'd call OpenAI Vision
        # But it's OPTIONAL - incident already exists!
        print(f"\n   [LLM would be called here if configured]")
        print(f"   [But incident is valid without it]")
    except Exception as e:
        print(f"\n   ⚠️  LLM failed: {e}")
        print(f"   ✅ But incident still exists with vision data!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Vision Gatekeeper")
    parser.add_argument("--image", required=True, help="Path to test image")
    parser.add_argument("--llm", action="store_true", help="Show LLM enrichment flow")
    
    args = parser.parse_args()
    
    # Run vision-first test
    success = test_gatekeeper_on_image(args.image)
    
    # Optionally show LLM enrichment
    if args.llm and success:
        test_with_llm_enrichment(args.image)
    
    print("\n" + "="*70)
    print("KEY TAKEAWAYS:")
    print("="*70)
    print("1. ✅ Vision detection happens FIRST (YOLO)")
    print("2. ✅ Rules score BEFORE any LLM")
    print("3. ✅ Gate decides eligibility (no LLM needed)")
    print("4. ✅ Structured incidents created WITHOUT LLM")
    print("5. ✅ LLM is OPTIONAL enrichment, not required")
    print("6. ✅ Training data based on detections, not captions")
    print("7. ✅ System works even if LLM fails")
    print("="*70)
