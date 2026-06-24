# 키보드 텔레오퍼레이션 가이드

OMX_F 팔 + LSM4-NK235630x 레일 시스템을 Isaac Sim에서 키보드로 제어하는 방법.

---

## 실행 방법

두 스크립트를 **동시에 실행할 필요 없음**. 터미널 1개로 순서대로:

```bash
# ① 최초 1회만: USD 파일 생성
./run_load_omx_f_rail.sh
# → "WebRTC livestream running." 출력되면 Ctrl+C 로 종료
# → model/omx_f_rail.usd 가 생성됨

# ② 이후 매번: 텔레오퍼 실행
./run_teleop_omx_rail.sh
```

`model/omx_f_rail.usd`가 이미 존재하면 ①은 건너뛰고 ②만 실행.  
URDF를 수정했을 때만 ①을 다시 실행해 USD를 재생성.

WebRTC 클라이언트로 `166.104.223.32` 접속 후 키보드 입력.  
→ WebRTC 접속 방법: [ISAAC_SIM_GUIDE.md](ISAAC_SIM_GUIDE.md)

---

## 키 바인딩

| 키 | 동작 | 범위 |
|---|---|---|
| `W` / `S` | 레일 전진 / 후진 | 0 – 630 mm |
| `A` / `D` | Joint1 베이스 회전 | 무제한 |
| `Q` / `E` | Joint2 숄더 | 무제한 |
| `↑` / `↓` | Joint3 엘보 | 무제한 |
| `←` / `→` | Joint4 포어암 | 무제한 |
| `Z` / `X` | Joint5 손목 롤 | 무제한 |
| `Space` | 그리퍼 토글 (열기/닫기) | — |
| `R` | 홈 포지션 리셋 | — |

**이동 속도:** 레일 3 mm/frame, 팔 0.02 rad/frame (physics 60 Hz 기준 약 180 mm/s, 1.2 rad/s)

---

## 로봇 구조

```
world (고정)
└── rail_base (레일 바디, 700×80×40 mm)
    └── [rail_joint: prismatic, X축, 0–630 mm]
        └── rail_cart (이동 카트)
            └── link0 (팔 베이스, 팔 위로 60 mm)
                ├── joint1 (Z축 회전)
                ├── joint2 (Y축)
                ├── joint3 (Y축)
                ├── joint4 (Y축)
                ├── joint5 (X축)
                └── gripper_joint_1 / _2 (Z축, mimic)
```

End-effector 프레임: `end_effector_link` (link5 끝 +92 mm)

---

## 스크립트 동작 원리

`teleop_omx_rail.py`:
1. `model/omx_f_rail.usd` 로드
2. `isaacsim.core.api.World` + `SingleArticulation` 으로 물리 시뮬레이션 초기화
3. `carb.input` 키보드 이벤트 구독 (WebRTC 클라이언트 입력 포워딩)
4. 매 프레임: held key → joint position delta → `robot.set_joint_positions()`
5. `world.step(render=True)` 로 물리 + 렌더링

load 스크립트(`load_omx_f_rail.py`)와 달리 `world.step()` 사용 → 실제 물리 적용.

---

## 자주 발생하는 문제

| 증상 | 원인 / 해결 |
|---|---|
| `FileNotFoundError: omx_f_rail.usd` | USD 미생성. `./run_load_omx_f_rail.sh` 먼저 실행 |
| 키 입력이 안 먹힘 | WebRTC 뷰어 창 클릭해서 포커스 확보 후 재시도 |
| `No ArticulationRootAPI found` | USD 생성 실패 가능성. USD 삭제 후 load 스크립트 재실행 |
| 팔이 중력에 떨어짐 | drive strength/damping 조정 필요 — `load_omx_f_rail.py`의 `default_drive_strength` 값 증가 |
| DOF 개수 불일치 출력 | 콘솔의 `DOFs:` 줄 확인. 순서가 달라도 이름 기반 매핑이라 동작에 무관 |
