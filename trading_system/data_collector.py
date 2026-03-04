#!/usr/bin/env python3
"""
자동 매매 시스템 - 데이터 수집 모듈
트레이더 마크 📊
"""

import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional
import json
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCollector:
    """주식 데이터 수집 클래스"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 한국 주식 티커 매핑 (예시)
        self.korean_stocks = {
            '삼성전자': '005930.KS',
            'SK하이닉스': '000660.KS',
            '네이버': '035420.KS',
            '카카오': '035720.KS',
            '현대차': '005380.KS',
            'LG에너지솔루션': '373220.KS',
        }
        
        # 해외 주식 티커
        self.global_stocks = {
            '애플': 'AAPL',
            '테슬라': 'TSLA',
            '마이크로소프트': 'MSFT',
            '아마존': 'AMZN',
            '구글': 'GOOGL',
            '엔비디아': 'NVDA',
        }
    
    def get_stock_data(self, ticker: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """주식 데이터 다운로드"""
        try:
            logger.info(f"데이터 수집 중: {ticker} ({period}, {interval})")
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"데이터 없음: {ticker}")
                return pd.DataFrame()
            
            # 기술적 지표 추가
            df = self.add_technical_indicators(df)
            
            # 데이터 저장
            self.save_data(ticker, df)
            
            return df
            
        except Exception as e:
            logger.error(f"데이터 수집 실패 {ticker}: {e}")
            return pd.DataFrame()
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 분석 지표 추가"""
        if df.empty:
            return df
        
        # 이동평균선
        df['MA5'] = ta.trend.sma_indicator(df['Close'], window=5)
        df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['MA60'] = ta.trend.sma_indicator(df['Close'], window=60)
        
        # RSI (상대강도지수)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_diff'] = macd.macd_diff()
        
        # 볼린저밴드
        bb = ta.volatility.BollingerBands(df['Close'])
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_middle'] = bb.bollinger_mavg()  # mband -> mavg로 변경
        df['BB_lower'] = bb.bollinger_lband()
        df['BB_width'] = bb.bollinger_wband()
        
        # 거래량 지표
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        
        # 변동성
        df['Volatility'] = df['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
        
        return df
    
    def save_data(self, ticker: str, df: pd.DataFrame):
        """데이터 저장"""
        if df.empty:
            return
        
        # CSV 저장
        filename = f"{self.data_dir}/{ticker.replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename)
        logger.info(f"데이터 저장 완료: {filename}")
        
        # 메타데이터 저장
        metadata = {
            'ticker': ticker,
            'last_updated': datetime.now().isoformat(),
            'data_points': len(df),
            'date_range': {
                'start': df.index[0].strftime('%Y-%m-%d'),
                'end': df.index[-1].strftime('%Y-%m-%d')
            }
        }
        
        metadata_file = f"{self.data_dir}/{ticker.replace('.', '_')}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def collect_multiple_stocks(self, tickers: List[str], period: str = "1mo") -> Dict[str, pd.DataFrame]:
        """여러 종목 데이터 수집"""
        results = {}
        
        for ticker in tickers:
            df = self.get_stock_data(ticker, period)
            if not df.empty:
                results[ticker] = df
                time.sleep(1)  # API 호출 간격 조절
        
        return results
    
    def get_realtime_data(self, ticker: str):
        """실시간 데이터 스트리밍 (웹소켓 필요)"""
        # TODO: 실시간 데이터 스트리밍 구현
        pass
    
    def generate_market_report(self):
        """시장 리포트 생성"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'korean_stocks': {},
            'global_stocks': {},
            'market_summary': {}
        }
        
        # 한국 주식 데이터 수집
        for name, ticker in self.korean_stocks.items():
            df = self.get_stock_data(ticker, period="5d", interval="1d")
            if not df.empty:
                last_close = df['Close'].iloc[-1]
                change = df['Close'].pct_change().iloc[-1] * 100
                report['korean_stocks'][name] = {
                    'ticker': ticker,
                    'price': float(last_close),
                    'change_percent': float(change),
                    'volume': int(df['Volume'].iloc[-1])
                }
        
        # 리포트 저장
        report_file = f"{self.data_dir}/market_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"시장 리포트 생성 완료: {report_file}")
        return report

def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("트레이더 마크 📊 - 데이터 수집 시스템 시작")
    print("=" * 50)
    
    collector = DataCollector()
    
    # 테스트: 삼성전자 데이터 수집
    print("\n1. 삼성전자 데이터 수집 테스트...")
    samsung_data = collector.get_stock_data('005930.KS', period="1mo")
    
    if not samsung_data.empty:
        print(f"수집된 데이터: {len(samsung_data)}개 봉")
        print(f"최근 종가: {samsung_data['Close'].iloc[-1]:,.0f}원")
        print(f"RSI: {samsung_data['RSI'].iloc[-1]:.2f}")
        print(f"변동성: {samsung_data['Volatility'].iloc[-1]:.2%}")
    
    # 여러 종목 데이터 수집
    print("\n2. 주요 종목 데이터 수집...")
    test_tickers = ['005930.KS', '000660.KS', '035420.KS']
    multiple_data = collector.collect_multiple_stocks(test_tickers, period="1mo")
    print(f"수집 완료: {len(multiple_data)}개 종목")
    
    # 시장 리포트 생성
    print("\n3. 시장 리포트 생성...")
    report = collector.generate_market_report()
    print(f"리포트 생성 완료: 한국주식 {len(report['korean_stocks'])}개")
    
    print("\n" + "=" * 50)
    print("데이터 수집 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()