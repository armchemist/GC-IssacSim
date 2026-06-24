# Isaac Sim 서버 설정 및 WebRTC 접속 가이드

GPU 서버에서 Isaac Sim을 headless로 실행하고, 로컬 PC에서 WebRTC로 화면을 보는 방법.

---

## 서버 환경

| 항목 | 값 |
|---|---|
| GPU | NVIDIA RTX 3080 ×2 |
| conda 환경 | `isaac_sim` (Isaac Sim 5.1) |
| 외부 IP | `166.104.223.32` |
| 스트리밍 포트 | `49100` |

**방화벽 개방이 필요한 포트** (외부망 접속 시):

| 프로토콜 | 포트 범위 |
|---|---|
| TCP/UDP | 47995–48012, 49000–49007, 49100 |
| TCP | 8211, 8011 |

같은 LAN·학교망·VPN 내부라면 별도 개방 불필요.

---

## 로컬 PC 준비

**Isaac Sim WebRTC Streaming Client** 설치:  
<https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_workstation.html#isaac-sim-webrtc-streaming-client>

서버와 동일한 Isaac Sim 버전(5.x)에 맞는 클라이언트 사용.

---

## 서버 접속

```bash
ssh jgshin22@166.104.223.32
cd /data1/workspaces/jgshin22/LabBot/IsaacSim
```

---

## Isaac Sim 실행

모든 런스크립트는 자동으로 `conda activate isaac_sim` + `CUDA_VISIBLE_DEVICES=1` 설정.

```bash
./run_isaacsim_livestream.sh      # 빈 씬
./run_load_omx_f.sh               # 팔 단독 뷰어
./run_load_omx_f_rail.sh          # 레일+팔 뷰어 (USD 생성 포함)
./run_teleop_omx_rail.sh          # 키보드 텔레오퍼레이션
```

**첫 실행은 shader 컴파일로 5–10분 소요.** 아래 메시지가 나오면 준비 완료:
```
Streaming server started.
```

종료: `Ctrl+C`  
백그라운드에서 종료: `pkill -f isaacsim` (다른 사용자 세션 주의)

---

## 로컬에서 WebRTC 접속

1. Isaac Sim WebRTC Streaming Client 실행
2. Server: `166.104.223.32` → **Connect**
3. Isaac Sim UI 표시됨

---

## 자주 발생하는 문제

| 증상 | 원인 / 해결 |
|---|---|
| 화면 검정 | 첫 실행 shader 컴파일 중. 콘솔 로그 확인하며 대기 |
| `Streaming server started.` 안 뜸 | 다른 프로세스가 GPU 점유. `nvidia-smi` 확인 |
| Connect timeout | 포트 미개방. `ss -tulnp \| grep 49100` 으로 LISTEN 확인 |
| GPU 메모리 부족 | `CUDA_VISIBLE_DEVICES=0` 또는 다른 빈 GPU로 변경 |
| `package://...` 경로 오류 | 이 프로젝트 URDF는 상대경로 사용 — 문제 없음 |
| USD 레이어 분리 · reference 깨짐 | 스크립트가 `open_stage(dest_path)` 로 직접 열도록 설계됨 |
| `World.step()` AttributeError | URDF import 직후 stage 교체됨. viewer 스크립트에선 `simulation_app.update()` 사용 |

---

## 참고

- Isaac Sim 공식 문서: <https://docs.isaacsim.omniverse.nvidia.com/>
- WebRTC 스트리밍: <https://docs.isaacsim.omniverse.nvidia.com/latest/installation/manual_livestream_clients.html>
- URDF 임포터: <https://docs.isaacsim.omniverse.nvidia.com/latest/robot_setup/import_urdf.html>
