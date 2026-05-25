# Isaac Sim 원격 사용 가이드 (SSH 서버 + WebRTC 스트리밍)

GPU 서버에 SSH로 접속해서 Isaac Sim을 띄우고, 로컬 PC에서 화면을 보는 방법입니다.
이 문서는 [LabBot](.) 환경 기준으로 작성되었습니다.

---

## 0. 사전 준비

### 서버 (이미 설정되어 있는 항목)
- Ubuntu + NVIDIA RTX GPU (현재: RTX 3080 ×2)
- NVIDIA 드라이버 + CUDA
- `conda env: isaac_sim` (Isaac Sim 5.1 설치됨)
- 외부 IP: `166.104.223.32`
- 사용 포트 (서버↔클라이언트 사이에 방화벽이 있을 때만 개방 필요):
  - TCP/UDP: `47995-48012`, `49000-49007`, `49100`
  - TCP: `8211`, `8011`

> **포트 개방이 필요한 경우**: 외부 인터넷(다른 ISP/집)에서 접속, 클라우드 VM(AWS/GCP), 또는 회사 방화벽이 있는 환경.
> **필요 없는 경우**: 서버와 로컬 PC가 같은 LAN/학교망 내부, VPN으로 접속 중, 또는 서버에 ufw/iptables가 꺼져있을 때 (`sudo ufw status` 로 확인).
>
> 위 항목이 안 되어 있으면 관리자에게 문의. 새 머신이라면 Isaac Sim 공식 [설치 가이드](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_workstation.html)를 참고하세요.

### 로컬 PC
- **Isaac Sim WebRTC Streaming Client** 설치
  - NVIDIA 다운로드 페이지: <https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_workstation.html#isaac-sim-webrtc-streaming-client>
  - OS에 맞는 버전 (Windows / Linux / macOS) 다운로드 후 설치
- 서버와 같은 네트워크에 있거나, 위 포트들이 외부에서 접근 가능해야 함

---

## 1. 서버 접속

```bash
ssh <user>@166.104.223.32
```

작업 디렉토리:
```bash
cd /data1/workspaces/jgshin22/LabBot
```

---

## 2. Isaac Sim 실행 (빈 씬)

`run_isaacsim_livestream.sh`로 headless + WebRTC 스트리밍 모드 실행:

```bash
./run_isaacsim_livestream.sh
```

내부적으로 하는 일:
1. `conda activate isaac_sim`
2. `CUDA_VISIBLE_DEVICES=1` (3080 #1번 GPU 사용)
3. `isaacsim isaacsim.exp.full.streaming.kit --no-window --/app/livestream/publicEndpointAddress=166.104.223.32 --/app/livestream/port=49100`

**첫 실행은 shader 컴파일에 5~10분** 걸립니다. 콘솔에 다음이 보이면 준비 완료:
```
Streaming server started.
```

> 끄려면 `Ctrl+C`.

---

## 3. 로컬 PC에서 접속

1. **Isaac Sim WebRTC Streaming Client** 실행
2. Server 입력란에 `166.104.223.32` 입력
3. **Connect** 클릭
4. 잠시 후 Isaac Sim UI가 보임 (빈 stage)

### 연결이 안 될 때
- 서버 콘솔에 `Streaming server started.` 떴는지 확인
- 포트 확인: `ss -tulnp | grep 49100`
- 방화벽 열려있는지 확인
- 클라이언트 버전이 서버 Isaac Sim 버전과 호환되는지 확인 (5.x ↔ 5.x)

---

## 4. URDF 임포트 (GUI에서)

스트리밍 클라이언트로 접속한 Isaac Sim 안에서:

1. 상단 메뉴 **File → Import**
2. URDF 파일 선택 (예: `/data1/workspaces/jgshin22/LabBot/omx_f.urdf`)
3. 임포트 옵션:
   - **Fix Base Link**: ✅ (로봇 바닥 고정)
   - **Merge Fixed Joints**: ⬜
   - **Self Collision**: ⬜
   - **Create Physics Scene**: ✅
   - Output Directory: 기본값
4. **Import** 클릭
5. 로봇이 viewport에 안 보이면:
   - 우측 **Stage** 패널에서 임포트된 prim 선택 → `F` 키 (Frame Selected)
   - 어두우면 **Create → Light → Distant Light** 추가

### URDF의 mesh 경로 주의
URDF가 `package://...` ROS 경로를 쓰면 Isaac Sim이 찾지 못합니다. 미리 절대경로로 바꿔두세요:

```bash
sed -i 's|package://my_package/|/absolute/path/to/my_package/|g' robot.urdf
```

---

## 5. (선택) 스크립트로 자동 임포트

매번 GUI로 임포트하기 귀찮으면 standalone Python 스크립트로 자동화 가능합니다. 예시: [load_omx_f.py](load_omx_f.py), [run_load_omx_f.sh](run_load_omx_f.sh).

핵심 구조:
```python
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})

from isaacsim.core.utils.extensions import enable_extension
enable_extension("omni.kit.livestream.webrtc")

import omni.kit.commands, omni.usd
from isaacsim.asset.importer.urdf import _urdf

cfg = _urdf.ImportConfig()
cfg.fix_base = True
cfg.create_physics_scene = True

_, robot = omni.kit.commands.execute("URDFParseFile", urdf_path="robot.urdf", import_config=cfg)
omni.kit.commands.execute("URDFImportRobot",
    urdf_path="robot.urdf", urdf_robot=robot,
    import_config=cfg, dest_path="robot.usd")

omni.usd.get_context().open_stage("robot.usd")

while simulation_app.is_running():
    simulation_app.update()
simulation_app.close()
```

실행 시 livestream kwargs를 같이 넘겨야 합니다:
```bash
python load_omx_f.py \
  --/app/livestream/publicEndpointAddress=166.104.223.32 \
  --/app/livestream/port=49100
```

---

## 6. 자주 발생하는 문제

| 증상 | 원인 / 해결 |
|---|---|
| 클라이언트 화면 검정 | 첫 실행 shader 컴파일 중. 콘솔 로그 확인하며 대기 |
| `Streaming server started.` 안 뜸 | 다른 프로세스가 GPU 점유 중일 수 있음. `nvidia-smi` 확인 |
| Connect timeout | 방화벽/포트 문제. `ss -tulnp \| grep 49100` 으로 LISTEN 확인 |
| `package://...` 못 찾음 | URDF mesh 경로 절대경로로 변경 |
| URDF importer가 USD 파일을 여러 layer로 쪼개고 reference 깨짐 | 스크립트에서 `open_stage(dest_path)`로 결과 USD를 직접 열기 |
| `World.step()` AttributeError | URDF import가 stage를 갈아끼움. `World` 대신 `simulation_app.update()` 루프 사용 |
| GPU 메모리 부족 | `CUDA_VISIBLE_DEVICES=1` 같이 빈 GPU 지정 |

---

## 7. 종료

서버 콘솔에서 `Ctrl+C`. 백그라운드로 띄웠다면 `pkill -f isaacsim` (다른 사용자 세션 죽이지 않도록 주의).

---

## 참고 자료
- Isaac Sim 공식 문서: <https://docs.isaacsim.omniverse.nvidia.com/>
- WebRTC Streaming: <https://docs.isaacsim.omniverse.nvidia.com/latest/installation/manual_livestream_clients.html>
- URDF Importer: <https://docs.isaacsim.omniverse.nvidia.com/latest/robot_setup/import_urdf.html>
