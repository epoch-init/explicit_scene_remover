def process_cuts(raw_cuts, target_labels, threshold, padding):
    """Filters, pads, and merges overlapping AI detections."""
    valid_cuts = []
    
    # 1. Filter by label and confidence, and apply padding
    for cut in raw_cuts:
        # Our AI models output "Nudity/NSFW" and "Profanity"
        if cut['label'] in target_labels and cut['confidence'] >= threshold:
            valid_cuts.append({
                'start': max(0.0, cut['start'] - padding),
                'end': cut['end'] + padding,
                'labels': [cut['label']] # List format to support merging later
            })
            
    if not valid_cuts:
        return []
        
    # 2. Sort chronologically
    valid_cuts.sort(key=lambda x: x['start'])
    
    # 3. Merge overlapping intervals
    merged_cuts = [valid_cuts[0]]
    
    for current in valid_cuts[1:]:
        prev = merged_cuts[-1]
        
        # If the current cut overlaps with the previous one
        if current['start'] <= prev['end']:
            prev['end'] = max(prev['end'], current['end'])
            # Combine unique labels (e.g., "Nudity/NSFW, Profanity")
            prev['labels'] = list(set(prev['labels'] + current['labels']))
        else:
            merged_cuts.append(current)
            
    # Format labels cleanly for UI rendering
    for cut in merged_cuts:
        cut['label'] = " & ".join(cut['labels'])
        del cut['labels']
        
    return merged_cuts
