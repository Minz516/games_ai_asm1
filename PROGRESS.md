# PROGRESS.md — COSC3145 Assignment 1 Checklist

> Nguồn: `../GAIT_Ass1-Description_Sem3 2025.pdf`. File này được tự động rà soát dựa trên nội dung
> code hiện tại trong `src/`. Các mục Performance/Tuning và Submission KHÔNG được tự động tick —
> chỉ người dùng mới xác nhận được (cần chạy game bằng mắt, hoặc biết đã quay video/nộp bài chưa).

## Part 1 — Steering Behaviours (steering.py)
- [x] A. Arrive: hàm `arrive()` slow dần trong slow_radius, dừng hẳn trong stop_radius, dùng dt, không overshoot/jitter
- [x] B. Boids Separation: hàm `boids_separation()` đẩy ra xa neighbor trong sep_radius *(đã implement — tính vector đẩy tỉ lệ nghịch khoảng cách trong sep_radius)*
- [x] B. Boids Cohesion: hàm `boids_cohesion()` kéo về trung bình vị trí neighbors *(đã implement — steer về center of mass của neighbors)*
- [x] B. Boids Alignment: hàm `boids_alignment()` khớp vận tốc trung bình neighbors *(đã implement — steer về average velocity của neighbors)*
- [x] B. Boids blend: 3 lực được kết hợp trong Flock state của fly.py *(fly.py dòng ~119-122 đã active, gọi thật `boids_separation/cohesion/alignment` với SEP/COH/ALI_WEIGHT, không còn placeholder)*
- [x] C. Flee: hàm `flee()` steer ngược hướng threat, mạnh hơn khi gần
- [x] D. Obstacle Avoidance: hàm `seek_with_avoid()` cast circle thẳng trước, nếu bị chặn thì xoay góc trái/phải tìm đường thông *(đã implement đầy đủ — kiểm tra corridor thẳng bằng `circlecast_hits_any_rect`, nếu bị chặn thì quét góc trái/phải theo `AVOID_ANGLE_INCREMENT` tới `AVOID_MAX_ANGLE`, fallback phanh nhẹ `-vel * 0.5` nếu mọi hướng đều bị chặn. Dùng trong cả 4 state của snake.py: Aggro, PatrolAway, PatrolHome, Harmless)*

## Part 2 — Finite State Machines (fly.py, snake.py)
- [x] A. Fly FSM: transition Flock <-> Fleeing dựa trên khoảng cách tới frog/bubbles, có timer chống flicker (`scare_timer`, `idle_timer` đã hoạt động)
- [x] B. Snake FSM: transition Patrol <-> Aggro dùng AGGRO_RANGE/DEAGGRO_RANGE, quay về home khi hết đuổi (logic transition có trong `snake.py update()`)
  - Transition `Aggro → Harmless` (cạnh `HitFrog`/bubble-hit trong sơ đồ FSM) được set từ bên ngoài (main.py bubble-hit và damage logic) — giờ đã được nối và active.

## Part 3 — Advanced AI Extensions (5 tính năng, mỗi cái 1 điểm)
- [x] A. Pursue: hàm `pursue()` dự đoán vị trí tương lai frog, thay seek trong Aggro state của snake *(steering.py: `pursue()` đã implement — predict `target_pos + target_vel*time_horizon` rồi seek tới điểm đó. Snake Aggro (snake.py dòng ~98) giờ gọi `pursue_with_avoid()` — hàm tự viết thêm, kết hợp logic prediction của `pursue()` với corridor-avoidance của `seek_with_avoid()` — nên vừa có prediction vừa né vật cản trong cùng 1 lệnh gọi. Tính là hoàn thành yêu cầu Pursue)*
- [x] B. Evade: hàm `evade()` dự đoán vị trí tương lai frog, thay flee trong Fleeing state của fly *(steering.py: `evade()` đã implement — cùng logic prediction, flee tới vị trí dự đoán của threat. fly.py Fleeing (dòng ~132) đã active gọi `evade(self.pos, self.vel, frog.pos, frog.vel, FLY_SPEED)`, dòng `flee()` cũ đã bị comment lại)*
- [x] C. Confused State: snake Aggro -> Harmless -> Confused, wander ngẫu nhiên có timer rồi về patrol *(transition Harmless→Confused→PatrolAway với timer đã có trong snake.py, `wander_force()` implement đầy đủ. main.py dòng ~120-125 giờ đã ACTIVE (không còn comment): bubble trúng snake Aggro sẽ gọi `s.set_state(SnakeState.Harmless)`, snake về home rồi tự chuyển Confused theo logic có sẵn trong `snake.py`. Đường vào Aggro→Harmless→Confused giờ có thể xảy ra thật trong gameplay)*
- [x] D. Idle State: fly chuyển sang Idle drift khi xa frog đủ lâu, wander nhẹ, quay lại Flock khi frog tới gần *(transition Flock↔Idle hoạt động độc lập, không phụ thuộc bubble/damage logic. fly.py Idle (dòng ~146) đã gọi thật `force, self.wander_angle = wander_force(self.vel, self.wander_angle, rng_seed=self._rng)` thay cho `force = V2()` placeholder cũ — hoàn thành và có thể quan sát được trong gameplay bình thường)*
- [x] E. Hurt State: frog va chạm snake Aggro -> mất 1 máu, flash/tint, bất tử ~1 giây *(frog.py đã có `hurt_timer`/`can_be_hurt()`/`start_hurt()`/flash trong `draw()`. main.py dòng ~131-139 giờ đã ACTIVE (không còn comment): khi snake Aggro chạm frog và `frog.can_be_hurt()`, gọi `health -= 1`, `frog.start_hurt()`, và pacify snake sang Harmless — state giờ được kích hoạt thật trong gameplay)*

## Game logic hỗ trợ (main.py)
- [x] Bubble hit logic: bubble trúng snake Aggro -> pop bubble + chuyển snake sang Harmless *(main.py dòng ~120-125 đã active, không còn comment — loop bubble/snake kiểm tra overlap bằng `(BUBBLE_RADIUS + s.radius) ** 2`, nếu snake đang Aggro thì `set_state(Harmless)`, bubble luôn bị pop `b.alive = False`)*
- [x] Damage logic: snake Aggro chạm frog -> trừ máu *(main.py dòng ~131-139 đã active, không còn comment — chỉ snake Aggro mới gây damage, dùng `frog.can_be_hurt()` để tránh trừ máu liên tục nhiều frame, sau khi trúng đòn: `health -= 1`, `frog.start_hurt()`, snake bị pacify về Harmless, và set `game_over/win=False` khi hết máu)*
- [x] Snake update được bật *(main.py dòng ~112-113: `for s in snakes: s.update(dt, frog)` đã active, không còn comment — snakes giờ patrol/aggro/né vật cản thật trong game loop)*
- [x] Health bar giảm đúng khi bị đánh, fly counter tăng khi ăn ruồi *(fly counter: `fly_count += 1` hoạt động. Health bar: giờ giảm đúng vì damage logic đã nối — `health -= 1` mỗi khi frog trúng đòn từ snake Aggro và có thể bị hurt)*
- [x] Game over screen: "You died!" khi hết máu, "You won!" khi đủ 10 ruồi, pause + nhấn R để restart *(đã implement đầy đủ trong main.py — dim overlay, message theo win/lose, restart bằng R)*

## Performance & Tuning (CẦN TEST THỦ CÔNG BẰNG MẮT — Claude Code không tự verify được)
- [ ] Arrive mượt: frog slow dần rõ ràng, dừng đúng điểm click, không overshoot, không rung tại điểm dừng — *cần tôi tự test/tự xác nhận*
- [ ] Arrive cho snake: snake patrol qua lại home/patrol_point mượt, không overshoot ở waypoint — *cần tôi tự test/tự xác nhận*
- [ ] Boids ổn định: flies tụ thành đàn tự nhiên, không dồn thành 1 cục, không tan rã lộn xộn — *cần tôi tự test/tự xác nhận*
- [ ] Flee mượt: ruồi chạy trốn mượt (không giật), đổi màu vàng->tím đúng lúc, quay lại flock khi an toàn — *cần tôi tự test/tự xác nhận*
- [ ] Obstacle avoidance: snake né vật cản trơn tru, không đứng khựng, không xuyên qua vật cản — *cần tôi tự test/tự xác nhận*
- [ ] FSM believable: các transition hợp lý, không flicker qua lại liên tục ở ranh giới range — *cần tôi tự test/tự xác nhận*
- [ ] Pursue/Evade: chuyển động dự đoán mượt, không giật — *cần tôi tự test/tự xác nhận*
- [ ] Confused/Idle/Hurt: có timer đúng, transition mượt, có phản hồi hình ảnh rõ ràng — *cần tôi tự test/tự xác nhận*
- [ ] FPS ổn định ~60, không lag/khựng khi nhiều agent cùng hoạt động — *cần tôi tự test/tự xác nhận*

## Việc cần dọn trước khi nộp
- [x] Xóa các dòng print() debug tạm trong code *(frog.py `update()` không còn dòng print debug nào)*
- [x] `seek_with_avoid()` đã implement thật, KHÔNG còn là stub *(đã implement — corridor cast + xoay góc + fallback phanh)*
- [x] Không còn hàm nào raise NotImplementedError *(`wander_force()` đã implement xong — không còn hàm stub nào trong steering.py)*
- [x] 2 hàm mới `arrive_with_avoid()`, `pursue_with_avoid()` trong steering.py đã được dùng thật *(snake.py Aggro dùng `pursue_with_avoid()`; PatrolAway/PatrolHome/Harmless dùng `arrive_with_avoid()` — thay cho cách cộng `arrive() + seek_with_avoid()` trước đây, giờ mỗi state chỉ có 1 lệnh steer duy nhất, không còn 2 lực xung đột nhau)*
- [x] Đã trả các giá trị settings.py về mức hợp lý (không còn giá trị test tạm như FROG_SPEED=4.0) *(các giá trị trong settings.py hiện đều hợp lý, không thấy dấu hiệu giá trị test tạm)*

## Submission (nộp trên Canvas)
- [ ] File .zip chứa toàn bộ code, chỉ làm việc trong thư mục A1_Starter (không đổi tên/di chuyển file) — *cần tôi tự xác nhận*
- [ ] Video demo quay đầy đủ theo thứ tự: — *cần tôi tự xác nhận*
  - [ ] Part 1: Task A (Arrive), B (Boids), C (Flee), D (Avoidance)
  - [ ] Part 2: Task A (Fly FSM), B (Snake FSM)
  - [ ] Part 3: Task A (Pursue), B (Evade), C (Confused), D (Idle), E (Hurt)
- [ ] Nộp đúng hạn (trễ -10%/ngày, quá 5 ngày = 0 điểm) — *cần tôi tự xác nhận*
- [ ] Nếu nộp trễ, báo cho giảng viên để họ tải đúng phiên bản — *cần tôi tự xác nhận*
