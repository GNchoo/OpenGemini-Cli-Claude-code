# Cloudflare Tunnel 운영안 (트레이더 대시보드)

## 현재 적용 상태 (임시)
- 서비스: `trader-cloudflared.service`
- 타입: Quick Tunnel (`trycloudflare.com`)
- 원본: `http://localhost:8080`
- 장점: 즉시 외부 접속 가능
- 제한: URL이 재시작 시 변경될 수 있음, Access 정책 미적용

현재 URL 확인:
```bash
~/.openclaw/workspace/trading_system/get_public_dashboard_url.sh
```

## 다음 단계 (권장: 고정 도메인 + Access)

### 1) Cloudflare 계정/도메인 준비
- Cloudflare에 도메인 연결
- Zero Trust 활성화

### 2) Named Tunnel 생성
```bash
~/.local/bin/cloudflared tunnel login
~/.local/bin/cloudflared tunnel create trader-dashboard
~/.local/bin/cloudflared tunnel route dns trader-dashboard trader-dashboard.<your-domain>
```

### 3) 토큰 기반 systemd 서비스로 전환
Cloudflare Dashboard에서 Tunnel Token 발급 후,
`~/.cloudflared/trader.env` 생성:
```bash
CF_TUNNEL_TOKEN=<발급받은_토큰>
```

예시 서비스:
```ini
[Unit]
Description=Trader Dashboard Cloudflare Named Tunnel
After=network-online.target trader-dashboard.service
Wants=network-online.target trader-dashboard.service

[Service]
Type=simple
EnvironmentFile=%h/.cloudflared/trader.env
ExecStart=%h/.local/bin/cloudflared tunnel --no-autoupdate run --token ${CF_TUNNEL_TOKEN}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

### 4) Access 정책 적용 (강력 권장)
- 허용 이메일만 접근
- One-time PIN 또는 SSO 로그인 필수
- 공개 URL이라도 인증 없이는 접근 불가

## 운영 체크
- `systemctl --user status trader-cloudflared.service`
- `journalctl --user -u trader-cloudflared.service -n 100 --no-pager`
- 대시보드 상태: `http://localhost:8080/api/health`
