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
│   ├── omx_f.usd               ↑ Isaac Sim USD (자동 생성)
│   ├── omx_f_rail.usd          ↑ Isaac Sim USD (자동 생성)
│   └── omx_f_mesh/             STL 메시
├── load_omx_f.py               팔 단독 뷰어
├── load_omx_f_rail.py          레일+팔 뷰어 / USD 생성
├── teleop_omx_rail.py          키보드 텔레오퍼레이션
├── run_isaacsim_livestream.sh  빈 Isaac Sim 실행
├── run_load_omx_f.sh           팔 단독 뷰어 실행
├── run_load_omx_f_rail.sh      레일+팔 뷰어 실행
├── run_teleop_omx_rail.sh      텔레오퍼 실행
└── docs/
    ├── ISAAC_SIM_GUIDE.md      서버 접속 · WebRTC 설정
    └── TELEOP_GUIDE.md         키보드 텔레오퍼레이션 가이드
```

---

## 빠른 시작

### 1. 빈 Isaac Sim (확인용)
```bash
./run_isaacsim_livestream.sh
```

### 2. 팔 단독 뷰어
```bash
./run_load_omx_f.sh
```

### 3. 레일 + 팔 키보드 텔레오퍼레이션
```bash
# USD 최초 생성 (1회만)
./run_load_omx_f_rail.sh   # "WebRTC livestream running." 뜨면 Ctrl+C

# 텔레오퍼 실행
./run_teleop_omx_rail.sh
```

서버 IP `166.104.223.32`, 포트 `49100` — WebRTC 클라이언트로 접속.  
→ 자세한 접속 방법: [docs/ISAAC_SIM_GUIDE.md](docs/ISAAC_SIM_GUIDE.md)  
→ 키 바인딩 · 아키텍처: [docs/TELEOP_GUIDE.md](docs/TELEOP_GUIDE.md)
