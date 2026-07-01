# LabBot — OMX_F + 레일 시뮬레이터

OpenMANIPULATOR-X Follower 팔 + LSM4-NK235630x 선형 레일 Isaac Sim 환경.

> 3D 프린팅 그리퍼 어태치먼트는 [armchemist/gripper-attachments](https://github.com/armchemist/gripper-attachments)로 이동됨.

---

## 파일 구조

```
IsaacSim/
├── model/
│   ├── omx_f.urdf              팔 단독 URDF
│   ├── omx_f_on_rail.urdf      레일 + 팔 통합 URDF
│   ├── omx_f_dual_on_rail.urdf 레일 + 팔 2개 (단일 카트) URDF
│   ├── omx_f.usd               ↑ Isaac Sim USD (자동 생성)
│   ├── omx_f_rail.usd          ↑ Isaac Sim USD (자동 생성)
│   ├── omx_f_dual_rail.usd     ↑ Isaac Sim USD (자동 생성)
│   └── omx_f_mesh/             STL 메시
├── load_omx_f.py               팔 단독 뷰어
├── load_omx_f_rail.py          레일+팔 뷰어 / USD 생성
├── teleop_omx_rail.py          키보드 텔레오퍼레이션
├── load_omx_f_dual_rail.py     레일+팔 2개 USD 생성 (+ 실험실 환경)
├── teleop_omx_dual_rail.py     듀얼팔 텔레오퍼 (+ 비커)
├── lab_scene.py                실험실 씬 헬퍼 (NVIDIA 환경 + 절차적 비커)
├── run_isaacsim_livestream.sh  빈 Isaac Sim 실행
├── run_load_omx_f.sh           팔 단독 뷰어 실행
├── run_load_omx_f_rail.sh      레일+팔 뷰어 실행
├── run_teleop_omx_rail.sh      텔레오퍼 실행
├── run_load_omx_f_dual_rail.sh 듀얼팔 USD 생성 실행
├── run_teleop_omx_dual_rail.sh 듀얼팔 텔레오퍼 실행
└── docs/
    ├── ISAAC_SIM_GUIDE.md      서버 접속 · WebRTC 설정
    └── TELEOP_GUIDE.md         키보드 텔레오퍼레이션 가이드
```

---

## 스크립트 역할

| 스크립트 | 역할 | 실행 빈도 |
|---|---|---|
| `run_isaacsim_livestream.sh` | 빈 Isaac Sim (씬 없음, 확인용) | 필요할 때만 |
| `run_load_omx_f.sh` | 팔 단독 뷰어 (물리 없음) | 필요할 때만 |
| `run_load_omx_f_rail.sh` | 레일+팔 USD 파일 생성 | **최초 1회만** |
| `run_teleop_omx_rail.sh` | 키보드 텔레오퍼레이션 | 매번 |
| `run_load_omx_f_dual_rail.sh` | 듀얼팔 USD 생성 (+ 실험실 환경) | **최초 1회만** |
| `run_teleop_omx_dual_rail.sh` | 듀얼팔 텔레오퍼 (+ 비커) | 매번 |

> `run_load_*.sh`와 `run_teleop_*.sh`는 동시에 실행하지 않아도 됨.  
> 터미널 1개로 순서대로 실행.

### 듀얼팔 + 실험실 씬

단일 카트에 OMX_F 팔 2개, NVIDIA 실내 환경 + 절차적 비커(rigid body)로 꾸민 버전.
`W`/`S`는 공유 레일(두 팔 동시), `1`/`2`/`Tab`으로 활성 팔 전환 후 관절 제어,
`Space` 활성 팔 그리퍼. 자세한 키맵·구조는 [docs/TELEOP_GUIDE.md](docs/TELEOP_GUIDE.md).

---

## 빠른 시작 — 텔레오퍼레이션

```bash
# 최초 1회: model/omx_f_rail.usd 생성
./run_load_omx_f_rail.sh
# "WebRTC livestream running." 출력되면 Ctrl+C 로 종료

# 이후 매번: 텔레오퍼 실행
./run_teleop_omx_rail.sh
```

WebRTC 클라이언트로 `166.104.223.32` 접속 후 키보드 입력.  
→ 접속 방법: [docs/ISAAC_SIM_GUIDE.md](docs/ISAAC_SIM_GUIDE.md)  
→ 키 바인딩: [docs/TELEOP_GUIDE.md](docs/TELEOP_GUIDE.md)
