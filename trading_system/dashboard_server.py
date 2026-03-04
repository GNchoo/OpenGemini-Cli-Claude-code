#!/usr/bin/env python3
"""
트레이더 마크 📊 대시보드 서버
- paper_portfolio.json 자동 새로고침 API 제공
- 정적 파일 서빙
"""
import http.server
import json
import os
import sys
from pathlib import Path

PORT = 8088
BASE_DIR = Path(__file__).parent

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        # API: 최신 포트폴리오 데이터
        if self.path == '/api/portfolio':
            self.send_portfolio()
            return
        # API: 헬스체크
        if self.path == '/api/health':
            self.send_json({'status': 'ok', 'server': '트레이더마크 대시보드'})
            return
        # 기본: 정적 파일
        if self.path == '/' or self.path == '':
            self.path = '/dashboard_fixed.html'
        super().do_GET()

    def send_portfolio(self):
        try:
            data_path = BASE_DIR / 'paper_portfolio.json'
            with open(data_path, 'r') as f:
                data = json.load(f)
            self.send_json(data)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # 접속 로그 간소화
        try:
            if args and len(args) > 0 and '/api/' not in str(args[0]):
                print(f"[대시보드] {self.address_string()} - {args[0]}")
        except:
            pass  # 로깅 오류 무시

if __name__ == '__main__':
    os.chdir(BASE_DIR)
    with http.server.ThreadingHTTPServer(('0.0.0.0', PORT), DashboardHandler) as httpd:
        print(f"📊 트레이더 마크 대시보드 서버 시작")
        print(f"   로컬: http://localhost:{PORT}")
        print(f"   외부: http://119.198.50.135:{PORT}")
        print(f"   종료: Ctrl+C")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버 종료")
