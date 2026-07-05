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

---

## 듀얼팔 + 실험실 씬 (omx_f_dual_rail)

레일 위 **단일 카트에 OMX_F 팔 2개**, NVIDIA 실내 환경 + 절차적 비커(rigid body)로 꾸민 버전.

```bash
# ① 최초 1회만: 듀얼 USD 생성 (+ 환경 reference)
./run_load_omx_f_dual_rail.sh
# → "WebRTC livestream running." 출력되면 Ctrl+C
# → model/omx_f_dual_rail.usd 생성

# ② 이후 매번: 듀얼 텔레오퍼
./run_teleop_omx_dual_rail.sh
```

두 팔이 **하나의 카트를 공유**하므로 `W`/`S`는 두 팔을 함께 이동. 팔 관절·그리퍼
키는 **활성 팔**에만 적용 — `1`/`2`(또는 `Tab`)로 활성 팔 전환.

| 키 | 동작 |
|---|---|
| `1` / `2` / `Tab` | 활성 팔 선택 (1 = 왼쪽, 2 = 오른쪽, Tab = 토글) |
| `W` / `S` | 공유 레일 전진 / 후진 (두 팔 동시) |
| `A`/`D`,`Q`/`E`,`↑`/`↓`,`←`/`→`,`Z`/`X` | 활성 팔 joint1–5 |
| `Space` | 활성 팔 그리퍼 토글 |
| `R` | 전체 홈 리셋 |

**관절 이름:** 단일팔과 달리 `l_`/`r_` 프리픽스 (예: `l_joint1`, `r_gripper_joint_1`),
레일은 공유라 `rail_joint` 그대로. 콘솔 `DOFs:` 줄에서 확인 가능 (~13 DOF).

### 씬 배치 (lab_scene.py)

`add_lab_environment()` → `place_robot_on_bench()` → `add_lab_glassware()` 순서로
런타임에 씬 구성 (USD에 bake 안 됨, 매 실행 재생성).

**벤치:** Simple_Room 기본 둥근 테이블(`table_low`)은 자동 비활성화되고, 사각
4-다리 벤치(`/World/LabBench`, 1.3×0.9 m, 상판 높이 0.30 m)가 원점에 생성됨.
크기·높이는 `lab_scene.BENCH_SIZE` / `DEFAULT_BENCH` 상수로 조정.

**로봇 배치:** `place_robot_on_bench()`가 로봇 루트에 Z −90° 회전 + 벤치 뒤쪽
가장자리로 이동 적용 → 레일이 벤치 한쪽 가장자리에 놓이고 두 팔이 **건너편(−Y)을
바라봄**. 팔 도달축·레일축이 동일(로컬 +X)이라 −90° 회전으로 건너편을 향하게 함.
위치는 `BENCH_EDGE_INSET` / `ROBOT_YAW_DEG`로 조정.

**유리기구 (도달범위 내 상판):**
- 비커 3개 — 반투명 rigid body 원기둥 (`spawn_beakers`).
- 시험관대 1개 — 정적 프레임(베이스+기둥4+상단 테두리), `add_test_tube_rack`.
- 시험관 5개 — 얇은 rigid body 원기둥, 랙 슬롯에 세워짐 (`spawn_test_tubes`).
그리퍼로 집기/넘어뜨리기 가능. 안 집히면 `lab_scene.py`의 `mass`/`radius`/collision 튜닝.

**환경:** NVIDIA `Simple_Room` USD reference. 에셋 서버 오프라인이면 환경만 건너뛰고
원점에 기본 벤치로 대체 (경고 출력). 다른 환경은 `lab_scene.ENV_REL_PATH` 수정.
