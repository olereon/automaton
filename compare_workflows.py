#!/usr/bin/env python3
"""Compare two workflow files to find differences"""

import json
import sys

with open('workflows/run-08-16-1.json', 'r') as f:
    file1 = json.load(f)
    
with open('workflows/run-08-16-2.json', 'r') as f:
    file2 = json.load(f)

# Compare top-level properties
print('=== TOP-LEVEL DIFFERENCES ===')
for key in set(list(file1.keys()) + list(file2.keys())):
    if key != 'actions':
        val1 = file1.get(key)
        val2 = file2.get(key)
        if val1 != val2:
            print(f'{key}:')
            print(f'  File 1: {val1}')
            print(f'  File 2: {val2}')

# Count actions
print(f'\n=== ACTION COUNT ===')
print(f'File 1: {len(file1.get("actions", []))} actions')
print(f'File 2: {len(file2.get("actions", []))} actions')

# Find specific differences in actions
actions1 = file1.get('actions', [])
actions2 = file2.get('actions', [])

print('\n=== KEY ACTION DIFFERENCES ===')

# Find upload_image differences
uploads1 = [a for a in actions1 if a.get('type') == 'upload_image']
uploads2 = [a for a in actions2 if a.get('type') == 'upload_image']

print('\n1. Image uploads:')
for i, (u1, u2) in enumerate(zip(uploads1, uploads2)):
    val1 = u1.get('value', '')
    val2 = u2.get('value', '')
    if val1 != val2:
        print(f'  Upload {i+1}:')
        print(f'    File 1: ...{val1[-25:]}')
        print(f'    File 2: ...{val2[-25:]}')

# Check for prompt differences
prompts1 = [a for a in actions1 if a.get('type') == 'input_text' and 'wizard' in a.get('value', '')]
prompts2 = [a for a in actions2 if a.get('type') == 'input_text' and 'wizard' in a.get('value', '')]

print('\n2. Text prompts:')
for i, (p1, p2) in enumerate(zip(prompts1, prompts2)):
    val1 = p1.get('value', '')
    val2 = p2.get('value', '')
    if val1 != val2:
        print(f'  Prompt {i+1}: DIFFERENT')
        print(f'    File 1: {val1[:50]}...')
        print(f'    File 2: {val2[:50]}...')
    else:
        print(f'  Prompt {i+1}: IDENTICAL')

# Find the extra actions in file 2
print('\n=== STRUCTURAL DIFFERENCES ===')
if len(actions2) > len(actions1):
    print(f'File 2 has {len(actions2) - len(actions1)} MORE actions than File 1')
    
    # Find where they differ
    for i in range(min(len(actions1), len(actions2))):
        if actions1[i] != actions2[i]:
            print(f'\nFirst difference at action index {i}:')
            print(f'  File 1 [{i}]: {actions1[i].get("type"):20} - {actions1[i].get("description")}')
            print(f'  File 2 [{i}]: {actions2[i].get("type"):20} - {actions2[i].get("description")}')
            
            # Show the next few actions to see the pattern
            print(f'\n  Context (next 3 actions in File 2):')
            for j in range(i, min(i+3, len(actions2))):
                print(f'    [{j}]: {actions2[j].get("type"):20} - {actions2[j].get("description")}')
            break

# Look for heart button clicks
heart_buttons1 = [i for i, a in enumerate(actions1) if 'heart' in a.get('description', '').lower()]
heart_buttons2 = [i for i, a in enumerate(actions2) if 'heart' in a.get('description', '').lower()]

print(f'\n=== HEART BUTTON CLICKS ===')
print(f'File 1: {len(heart_buttons1)} clicks at indices {heart_buttons1}')
print(f'File 2: {len(heart_buttons2)} clicks at indices {heart_buttons2}')

# Summary
print('\n=== SUMMARY ===')
print('The files differ in:')
print('1. Image paths (different file numbers)')
print('2. File 2 has 2 additional actions (heart button click + wait)')
print('3. Both files have identical text prompts')
print('4. Both files have keep_browser_open: false')