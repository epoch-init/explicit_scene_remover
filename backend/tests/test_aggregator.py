from utils.aggregator import process_cuts

def test_process_cuts():
    raw = [
        {'start': 10.0, 'end': 15.0, 'label': 'Profanity', 'confidence': 0.9},
        {'start': 14.0, 'end': 20.0, 'label': 'Nudity/NSFW', 'confidence': 0.85},
        {'start': 50.0, 'end': 55.0, 'label': 'Profanity', 'confidence': 0.4}, # Low confidence
        {'start': 100.0, 'end': 105.0, 'label': 'Makeout', 'confidence': 0.9}  # Unwanted label
    ]
    
    # Threshold 0.5, Padding 2 seconds, Target only Profanity and Nudity
    results = process_cuts(
        raw_cuts=raw, 
        target_labels=['Profanity', 'Nudity/NSFW'], 
        threshold=0.5, 
        padding=2.0
    )
    
    assert len(results) == 1
    # Merged first two: start(10-2=8), end(20+2=22)
    assert results[0]['start'] == 8.0
    assert results[0]['end'] == 22.0
    assert "Profanity" in results[0]['label']
    assert "Nudity/NSFW" in results[0]['label']
