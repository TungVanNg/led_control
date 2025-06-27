# LED Hand Gesture Control - PHIÊN BẢN SỬA LỖI NGÓN GIỮA
# Sửa lỗi: Ngón giữa thả xuống LED vẫn sáng

import cv2
import mediapipe as mp
import serial
import time
import numpy as np
import threading
from queue import Queue
from collections import Counter, deque

class HandGestureController:
    def __init__(self, port='COM5', baudrate=115200):
        # Khoi tao MediaPipe voi cau hinh toi uu chong loa sang
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.65
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Khoi tao Serial
        self.serial_connected = False
        self.arduino = None
        self.init_serial(port, baudrate)
        
        # Bien trang thai
        self.current_gesture = "none"
        self.last_command = ""
        self.gesture_history = deque(maxlen=15)
        self.stable_frames = 0
        self.required_frames = 12
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # THÊM: Theo dõi trạng thái từng ngón tay
        self.finger_states = {
            'thumb': False,
            'index': False, 
            'middle': False,
            'ring': False,
            'pinky': False
        }
        self.last_finger_states = self.finger_states.copy()
        
        # Confidence tracking
        self.finger_confidence = {
            'thumb': deque(maxlen=8),
            'index': deque(maxlen=8), 
            'middle': deque(maxlen=8),
            'ring': deque(maxlen=8),
            'pinky': deque(maxlen=8)
        }
        
        # Bien chong loa sang
        self.brightness_history = deque(maxlen=10)
        self.last_detection_time = 0
        self.detection_cooldown = 0.3
        
        # Queue cho serial communication
        self.command_queue = Queue()
        self.start_serial_thread()
        
        # ARDUINO COMMAND MAPPING - Cho 5 LED tím
        self.gesture_commands = {
            "all_on": "ALL_ON",         # Sang tat ca
            "all_off": "ALL_OFF",       # Tat het
            "blink": "BLINK",           # Nhap nhay
            "running": "CHASE",         # Chay sang
            "breathing": "BREATHE",     # Hieu ung tho
            "rainbow": "RAINBOW",       # Cau vong
            "wave": "WAVE",             # Song
            "fade": "FADE",             # Fade
            "strobe": "STROBE",         # Nhap nhanh
            "twinkle": "TWINKLE"        # Long lanh
        }
        
        # Palette màu dịu mắt - Tone xanh lá nhạt và xám
        self.colors = {
            'bg': (45, 55, 45),           # Xanh lá đậm nhẹ
            'panel': (60, 75, 60),        # Xanh lá panel
            'accent': (120, 200, 120),    # Xanh lá sáng
            'success': (80, 180, 100),    # Xanh lục
            'warning': (200, 170, 80),    # Vàng nhạt
            'danger': (200, 100, 100),    # Đỏ nhạt
            'text': (240, 245, 240),      # Trắng nhẹ
            'text_dim': (180, 190, 180),  # Xám nhạt
            'hand': (100, 200, 150),      # Xanh mint
            'joint': (150, 120, 200)      # Tím nhạt
        }

    def init_serial(self, port, baudrate):
        """Khoi tao ket noi serial"""
        try:
            self.arduino = serial.Serial(port, baudrate, timeout=0.1)
            time.sleep(2)
            self.serial_connected = True
            print(f"✓ Arduino connected: {port}")
        except Exception as e:
            self.serial_connected = False
            print(f"✗ Arduino error: {e}")

    def start_serial_thread(self):
        """Thread xu ly serial"""
        def serial_worker():
            while True:
                try:
                    if not self.command_queue.empty() and self.serial_connected:
                        command = self.command_queue.get()
                        self.arduino.write(f"{command}\n".encode())
                        time.sleep(0.1)
                except:
                    pass
                time.sleep(0.02)
        
        if self.serial_connected:
            threading.Thread(target=serial_worker, daemon=True).start()

    def check_brightness_overload(self, frame):
        """Kiem tra va xu ly loa sang"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        self.brightness_history.append(avg_brightness)
        
        if len(self.brightness_history) >= 5:
            recent_brightness = np.mean(list(self.brightness_history)[-5:])
            if recent_brightness > 180:
                return True
        return False

    def count_fingers_anti_glare(self, landmarks):
        """Dem ngon tay - Chong loa sang"""
        if not landmarks:
            return [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]
        
        tips = [4, 8, 12, 16, 20]
        pip_joints = [3, 6, 10, 14, 18]
        
        fingers = []
        confidences = []
        
        for i in range(5):
            if i == 0:  # Ngon cai
                tip_x = landmarks[tips[i]].x
                pip_x = landmarks[pip_joints[i]].x
                finger_up = tip_x > pip_x
                conf = 0.8 if finger_up else 0.2
            else:  # 4 ngon con lai
                tip_y = landmarks[tips[i]].y
                pip_y = landmarks[pip_joints[i]].y
                finger_up = tip_y < pip_y
                conf = 0.8 if finger_up else 0.2
            
            fingers.append(1 if finger_up else 0)
            confidences.append(conf)
        
        return fingers, confidences

    def detect_gesture_stable(self, fingers):
        """Nhan dien cu chi on dinh"""
        finger_count = sum(fingers)
        
        if finger_count == 5:
            return "all_on"
        elif finger_count == 0:
            return "all_off"
        elif fingers == [1, 0, 0, 0, 0]:
            return "blink"
        elif fingers == [0, 1, 0, 0, 0]:
            return "running"
        elif fingers == [0, 0, 1, 0, 0]:
            return "breathing"
        elif fingers == [0, 0, 0, 1, 0]:
            return "rainbow"
        elif fingers == [0, 0, 0, 0, 1]:
            return "wave"
        elif fingers == [1, 1, 0, 0, 0]:
            return "fade"
        elif fingers == [0, 1, 1, 0, 0]:
            return "strobe"
        elif finger_count == 3:
            return "twinkle"
        else:
            return "none"

    def update_finger_states(self, fingers):
        """SỬA LỖI: Cập nhật và theo dõi trạng thái từng ngón tay"""
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
        
        # Lưu trạng thái cũ
        self.last_finger_states = self.finger_states.copy()
        
        # Cập nhật trạng thái mới
        for i, name in enumerate(finger_names):
            self.finger_states[name] = bool(fingers[i])
        
        # DEBUG: In ra thay đổi trạng thái ngón giữa
        if self.last_finger_states['middle'] != self.finger_states['middle']:
            status = "UP" if self.finger_states['middle'] else "DOWN"
            print(f"MIDDLE FINGER: {status}")

    def send_command_stable(self, gesture, fingers):
        """SỬA LỖI: Gui lenh on dinh - Xử lý riêng từng ngón tay"""
        current_time = time.time()
        
        # Cập nhật trạng thái ngón tay
        self.update_finger_states(fingers)
        
        # SỬA LỖI CHÍNH: Kiểm tra tất cả ngón tay - Tắt ngay khi có ngón nào thả
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
        for finger_name in finger_names:
            if self.last_finger_states[finger_name] and not self.finger_states[finger_name]:
                # Ngón tay vừa thả xuống -> Tắt LED ngay lập tức
                print(f"→ {finger_name.upper()} DOWN - FORCE STOP")
                self.command_queue.put("ALL_OFF")
                self.last_command = "ALL_OFF"
                self.gesture_history.clear()  # Clear history để reset
                self.current_gesture = "none"  # Force reset gesture
                return
        
        # SỬA LỖI: Nếu không có ngón nào duỗi thì tắt hết
        if sum(fingers) == 0:
            if self.last_command != "ALL_OFF":
                print("→ NO FINGERS UP - ALL OFF")
                self.command_queue.put("ALL_OFF")
                self.last_command = "ALL_OFF"
                self.current_gesture = "none"
            return
        
        # SỬA LỖI: Nếu gesture = none nhưng vẫn có ngón duỗi
        if gesture == "none" and sum(fingers) > 0:
            if self.last_command != "ALL_OFF":
                print("→ UNDEFINED GESTURE - ALL OFF")
                self.command_queue.put("ALL_OFF")
                self.last_command = "ALL_OFF"
                self.current_gesture = "none"
            return
        
        # Xử lý gesture mới
        if gesture != "none":
            # Kiem tra stability - giảm yêu cầu để phản ứng nhanh hơn
            self.gesture_history.append(gesture)
            if len(self.gesture_history) < 3:  # Giảm từ 5 xuống 3
                return
            
            # Chi can 50% consistency - giảm để nhạy hơn
            gesture_counts = Counter(self.gesture_history)
            most_common = gesture_counts.most_common(1)[0]
            stability = most_common[1] / len(self.gesture_history)
            
            if stability >= 0.5 and most_common[0] == gesture:  # Giảm từ 0.6 xuống 0.5
                arduino_cmd = self.gesture_commands.get(gesture, "")
                
                # Chỉ gửi lệnh nếu khác lệnh cuối
                if arduino_cmd and arduino_cmd != self.last_command:
                    self.command_queue.put(arduino_cmd)
                    self.last_command = arduino_cmd
                    self.current_gesture = gesture
                    self.last_detection_time = current_time
                    print(f"→ NEW GESTURE: {arduino_cmd}")
                    self.gesture_history.clear()

    def draw_compact_interface(self, frame, gesture, fingers):
        """Giao dien compact - Chu nho va mau diu mat"""
        h, w = frame.shape[:2]
        
        # Tao background diu mat chi o cac goc
        cv2.rectangle(frame, (0, 0), (w, 100), self.colors['bg'], -1)  # Top area
        cv2.rectangle(frame, (0, h-80), (w, h), self.colors['bg'], -1)  # Bottom area
        
        # Header sạch sẽ - XÓA dòng trùng lặp
        cv2.rectangle(frame, (0, 0), (w, 40), self.colors['panel'], -1)
        cv2.putText(frame, "LED Hand Control v2.4 - Pin: 2,4,5,18,19", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
        
        # Status
        status_color = self.colors['success'] if self.serial_connected else self.colors['danger']
        cv2.circle(frame, (w-30, 20), 8, status_color, -1)
        cv2.putText(frame, f"FPS:{self.fps:.0f}", (w-80, 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colors['text_dim'], 1)
        
        # Gesture display - compact
        gesture_names = {
            "all_on": "TAT CA SANG", "all_off": "TAT HET", "blink": "NHAP NHAY",
            "running": "CHAY SANG", "breathing": "THO", "rainbow": "CAU VONG",
            "wave": "SONG", "fade": "MO DAN", "strobe": "NHAP NHANH", 
            "twinkle": "LONG LANH", "none": "CHO LENH..."
        }
        
        display_name = gesture_names.get(gesture, "KHONG RO")
        text_color = self.colors['accent'] if gesture != "none" else self.colors['text_dim']
        
        # Main gesture box
        cv2.rectangle(frame, (10, 50), (220, 90), self.colors['panel'], -1)
        cv2.putText(frame, display_name, (15, 75), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.55, text_color, 2)
        
        # Finger status - minimal với chỉ báo thay đổi
        finger_names = ["C", "T", "G", "A", "U"]  # Cai, Tro, Giua, Ap, Ut
        for i, (name, status) in enumerate(zip(finger_names, fingers)):
            x = 240 + i * 28
            
            # SỬA LỖI: Highlight ngón tay vừa thay đổi
            finger_key = ['thumb', 'index', 'middle', 'ring', 'pinky'][i]
            just_changed = self.last_finger_states[finger_key] != self.finger_states[finger_key]
            
            if just_changed:
                color = self.colors['warning']  # Màu cảnh báo khi thay đổi
            else:
                color = self.colors['success'] if status else self.colors['panel']
            
            cv2.circle(frame, (x, 70), 11, color, -1)
            cv2.putText(frame, name, (x-4, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, 
                       self.colors['text'], 1)
        
        # Quick guide - Tieng Viet khong dau, chu nho
        guide_y = h - 70
        cv2.rectangle(frame, (0, guide_y), (w, h), self.colors['bg'], -1)
        
        guides = [
            "5 ngon->sang het", "nam tay->tat", "ngon cai->nhap nhay", "ngon tro->chay sang",
            "ngon giua->tho", "ngon ap->cau vong", "ngon ut->song", "2 ngon->mo dan"
        ]
        
        # Hiển thị hướng dẫn
        for i, guide in enumerate(guides[:4]):
            x = 5 + i * 150
            cv2.putText(frame, guide, (x, guide_y + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.colors['text'], 1)
        
        for i, guide in enumerate(guides[4:]):
            x = 5 + i * 150
            cv2.putText(frame, guide, (x, guide_y + 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.colors['text'], 1)

    def draw_hand_minimal(self, frame, landmarks):
        """Ve tay minimal - it noi bat hon"""
        if landmarks:
            self.mp_draw.draw_landmarks(
                frame, landmarks, self.mp_hands.HAND_CONNECTIONS,
                self.mp_draw.DrawingSpec(color=self.colors['hand'], thickness=1, circle_radius=1),
                self.mp_draw.DrawingSpec(color=self.colors['joint'], thickness=1, circle_radius=2)
            )

    def calculate_fps(self):
        """Tinh FPS"""
        self.frame_count += 1
        if time.time() - self.start_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.start_time = time.time()

    def run(self):
        """Chay chuong trinh chinh"""
        # Camera setup - Ty le 4:3 chuan
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.4)
        cap.set(cv2.CAP_PROP_CONTRAST, 0.6)
        cap.set(cv2.CAP_PROP_EXPOSURE, -6)
        
        if not cap.isOpened():
            print("Camera error!")
            return
        
        print("=" * 50)
        print("LED HAND CONTROL v2.4 - FIXED MIDDLE FINGER")
        print("=" * 50)
        print("✓ Fixed: Middle finger release stops LED immediately")
        print("✓ Fixed: All fingers release detection")
        print("✓ Added: Finger state change highlighting")
        print("✓ Camera: 640x480 (4:3 ratio)")
        print("✓ 5 Purple LEDs control")
        print("=" * 50)
        
        window_name = 'LED Hand Control - Fixed v2.4'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 640, 480)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            
            # Kiem tra loa sang
            is_overexposed = self.check_brightness_overload(frame)
            
            # Xu ly MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            gesture = "none"
            fingers = [0, 0, 0, 0, 0]
            
            if results.multi_hand_landmarks and not is_overexposed:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.draw_hand_minimal(frame, hand_landmarks)
                    fingers, _ = self.count_fingers_anti_glare(hand_landmarks.landmark)
                    gesture = self.detect_gesture_stable(fingers)
            else:
                # SỬA LỖI: Khi không detect được tay -> Force tắt LED
                if self.last_command != "ALL_OFF":
                    print("→ NO HAND DETECTED - FORCE OFF")
                    self.command_queue.put("ALL_OFF")
                    self.last_command = "ALL_OFF"
                    self.current_gesture = "none"
                    self.gesture_history.clear()
            
            # SỬA LỖI: Truyền thêm fingers vào send_command_stable
            self.send_command_stable(gesture, fingers)
            
            # Ve UI compact
            self.draw_compact_interface(frame, gesture, fingers)
            
            # Hien thi canh bao loa sang
            if is_overexposed:
                cv2.rectangle(frame, (200, 50), (440, 90), self.colors['danger'], 2)
                cv2.putText(frame, "QUA SANG - GIAM SANG", (210, 75), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['danger'], 1)
            
            self.calculate_fps()
            cv2.imshow(window_name, frame)
            
            # Controls
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('t'):
                if self.serial_connected:
                    self.command_queue.put("TEST")
            elif key == ord('r'):
                self.gesture_history.clear()
                # Reset finger states
                self.finger_states = {k: False for k in self.finger_states}
                self.last_finger_states = self.finger_states.copy()
        
        cap.release()
        cv2.destroyAllWindows()
        if self.serial_connected:
            self.arduino.close()
        print("✓ Program ended successfully!")

if __name__ == "__main__":
    controller = HandGestureController(port='COM5', baudrate=115200)
    controller.run()