import cv2
import threading
import pygame.midi
import time
from cvzone.HandTrackingModule import HandDetector

# Initialize MIDI
pygame.midi.init()
player = pygame.midi.Output(0)
player.set_instrument(0)  # Acoustic Grand Piano

# Initialize Camera
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width
cap.set(4, 720)   # Height
detector = HandDetector(detectionCon=0.85, maxHands=1)

# Chord Configuration (D Major Scale)
CHORDS = {
    "index": [62, 66, 69],   # D Major (D, F#, A)
    "middle": [67, 71, 74],  # G Major (G, B, D)
    "pinky": [69, 73, 76]    # A Major (A, C#, E)
}

# System Parameters
SUSTAIN_DURATION = 1.5
ACTIVE_NOTES = set()
FINGER_COLORS = [(0, 255, 0), (0, 0, 255), (0, 255, 255)]  # Green, Blue, Cyan
FINGER_NAMES = ["D Major", "G Major", "A Major"]

# Initialize gesture tracking
prev_gestures = {finger: 0 for finger in CHORDS}

def play_chord(notes):
    global ACTIVE_NOTES
    for note in notes:
        if note not in ACTIVE_NOTES:
            player.note_on(note, 127)
            ACTIVE_NOTES.add(note)

def stop_chord(notes):
    global ACTIVE_NOTES
    time.sleep(SUSTAIN_DURATION)
    for note in notes:
        if note in ACTIVE_NOTES:
            player.note_off(note, 127)
            ACTIVE_NOTES.remove(note)

def draw_finger_highlights(img, hand):
    lmList = hand["lmList"]
    fingers = {
        "index": lmList[8][:2],   # Index finger tip (x, y)
        "middle": lmList[12][:2], # Middle finger tip
        "pinky": lmList[20][:2]   # Pinky finger tip
    }
    
    for idx, (finger, tip) in enumerate(fingers.items()):
        color = FINGER_COLORS[idx] if detector.fingersUp(hand)[list(fingers.keys()).index(finger)+1] else (50, 50, 50)
        cv2.circle(img, tuple(tip), 25, color, cv2.FILLED)
        cv2.circle(img, tuple(tip), 25, (255, 255, 255), 2)

while True:
    success, img = cap.read()
    if not success:
        continue
    
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)
    
    current_gestures = {finger: 0 for finger in CHORDS}
    
    if hands:
        main_hand = hands[0]
        fingers_up = detector.fingersUp(main_hand)
        
        # Get 2D coordinates for distance check
        index_tip = main_hand["lmList"][8][:2]
        index_pip = main_hand["lmList"][5][:2]
        middle_tip = main_hand["lmList"][12][:2]
        middle_pip = main_hand["lmList"][9][:2]
        pinky_tip = main_hand["lmList"][20][:2]
        pinky_pip = main_hand["lmList"][17][:2]
        
        # Finger detection with distance threshold
        current_gestures["index"] = 1 if fingers_up[1] and \
            detector.findDistance(index_tip, index_pip)[0] > 50 else 0
        
        current_gestures["middle"] = 1 if fingers_up[2] and \
            detector.findDistance(middle_tip, middle_pip)[0] > 50 else 0
        
        current_gestures["pinky"] = 1 if fingers_up[4] and \
            detector.findDistance(pinky_tip, pinky_pip)[0] > 50 else 0
        
        draw_finger_highlights(img, main_hand)

    # Chord activation logic
    for finger in CHORDS:
        if current_gestures[finger] and not prev_gestures[finger]:
            play_chord(CHORDS[finger])
        elif not current_gestures[finger] and prev_gestures[finger]:
            threading.Thread(target=stop_chord, args=(CHORDS[finger],)).start()
    
    prev_gestures = current_gestures.copy()
    
    # Display Information
    cv2.putText(img, "Air Piano Pro - D Scale", (20, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Finger Legend
    for i, (color, name) in enumerate(zip(FINGER_COLORS, FINGER_NAMES)):
        cv2.rectangle(img, (1000, 50 + i*60), (1030, 80 + i*60), color, -1)
        cv2.putText(img, name, (1040, 80 + i*60), 
                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    cv2.imshow("Air Piano Pro", img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
for note in ACTIVE_NOTES:
    player.note_off(note, 127)
player.close()
pygame.midi.quit()
cap.release()
cv2.destroyAllWindows()