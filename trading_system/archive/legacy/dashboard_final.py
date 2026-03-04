            })
            .catch(() => {
                document.getElementById('networkUrl').textContent = 'http://[로컬IP]:8088 (IP 확인 실패)';
            });
    })
    .catch(() => {
        document.getElementById('networkUrl').textContent = '서버 연결 확인 중...';
    });

async function loadData() {
    try {
        console.log('🔄 데이터 로드 시작:', new Date().toLocaleTimeString());
        
        // 캐시 방지
        const timestamp = new Date().getTime();
        const response = await fetch(`/api/portfolio?t=${timestamp}`, {
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('✅ 데이터 로드 완료:', data.last_updated);
        
        updateDisplay(data);
        return data;
        
    } catch (error) {
        console.error('❌ 데이터 로드 실패:', error);
        document.getElementById('timestamp').innerHTML = 
            `<span style="color: #f87171;">오류: ${error.message}</span>`;
        return null;
    }
}

function updateDisplay(data) {
    // 자본 정보
    const capital = data.capital || 0;
    const initial = 1000000;
    const totalReturn = ((capital - initial) / initial * 100).toFixed(2);
    
    document.getElementById('capital').textContent = capital.toLocaleString('ko-KR') + '원';
    document.getElementById('capitalChange').textContent = `${totalReturn >= 0 ? '+' : ''}${totalReturn}%`;
    document.getElementById('capitalChange').className = `change ${totalReturn >= 0 ? 'positive' : 'negative'}`;
    
    // 수익률
    const dailyLog = data.daily_log || [];
    let totalReturnRate = 0;
    if (dailyLog.length > 0) {
        totalReturnRate = dailyLog[dailyLog.length - 1].total_return || 0;
    }
    document.getElementById('returnRate').textContent = totalReturnRate.toFixed(2) + '%';
    document.getElementById('returnChange').textContent = totalReturnRate >= 0 ? '📈 상승 중' : '📉 하락 중';
    document.getElementById('returnChange').className = `change ${totalReturnRate >= 0 ? 'positive' : 'negative'}`;
    
    // 거래 정보
    const tradeLog = data.trade_log || [];
    const today = new Date().toISOString().split('T')[0];
    const todayTrades = tradeLog.filter(t => t.date && t.date.startsWith(today)).length;
    
    document.getElementById('tradeCount').textContent = tradeLog.length + '회';
    document.getElementById('todayTrades').textContent = todayTrades;
    
    // 승률
    const profitableTrades = tradeLog.filter(t => (t.profit || 0) > 0).length;
    const winRate = tradeLog.length > 0 ? (profitableTrades / tradeLog.length * 100).toFixed(1) : 0;
    
    document.getElementById('winRate').textContent = winRate + '%';
    document.getElementById('winTrades').textContent = profitableTrades;
    
    // 수수료
    let totalFee = 0;
    tradeLog.forEach(t => {
        if (t.total_fee) totalFee += t.total_fee;
        else if (t.buy_fee && t.sell_fee) totalFee += (t.buy_fee + t.sell_fee);
    });
    
    document.getElementById('totalFee').textContent = Math.round(totalFee).toLocaleString('ko-KR') + '원';
    document.getElementById('avgFee').textContent = tradeLog.length > 0 ? Math.round(totalFee / tradeLog.length) : 0;
    
    // 거래 테이블
    updateTradeTable(tradeLog);
    
    // 타임스탬프
    updateTimestamp(data.last_updated);
}

function updateTradeTable(tradeLog) {
    const tbody = document.getElementById('tradeTableBody');
    const recentTrades = tradeLog.slice(-20).reverse(); // 최근 20개, 최신순
    
    if (recentTrades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #94a3b8;">거래 내역이 없습니다</td></tr>';
        return;
    }
    
    let html = '';
    recentTrades.forEach(trade => {
        const date = new Date(trade.date || Date.now());
        const timeStr = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
        
        const sideClass = trade.side === 'BUY' ? 'buy' : 'sell';
        const sideText = trade.side === 'BUY' ? '매수' : '매도';
        const sideEmoji = trade.side === 'BUY' ? '🟢' : '🔴';
        
        const profit = trade.profit || 0;
        const profitClass = profit >= 0 ? 'profit' : 'loss';
        const profitText = profit >= 0 ? `+${profit.toFixed(1)}` : profit.toFixed(1);
        
        html += `
            <tr>
                <td>${timeStr}</td>
                <td>${trade.symbol || 'N/A'}</td>
                <td><span class="status-badge ${sideClass}">${sideEmoji} ${sideText}</span></td>
                <td>${(trade.price || 0).toLocaleString('ko-KR')}원</td>
                <td>${(trade.volume || 0).toFixed(6)}</td>
                <td class="${profitClass}">${profitText}원</td>
                <td>${trade.reason || 'AI'}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function updateTimestamp(lastUpdated) {
    if (!lastUpdated) {
        document.getElementById('timestamp').textContent = '업데이트 시간 없음';
        document.getElementById('lastUpdated').textContent = '시간 정보 없음';
        return;
    }
    
    const updated = new Date(lastUpdated);
    const now = new Date();
    const diffMs = now - updated;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    
    let timeText;
    if (diffSec < 60) {
        timeText = `${diffSec}초 전`;
    } else if (diffMin < 60) {
        timeText = `${diffMin}분 전`;
    } else {
        timeText = updated.toLocaleTimeString('ko-KR');
    }
    
    document.getElementById('timestamp').textContent = `마지막 업데이트: ${timeText}`;
    document.getElementById('lastUpdated').textContent = updated.toLocaleString('ko-KR');
}

// 자동 새로고침 시작/중지
function startAutoRefresh(interval = 10000) {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    autoRefreshInterval = setInterval(loadData, interval);
    console.log(`🔄 자동 새로고침 시작: ${interval/1000}초 간격`);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('⏹️ 자동 새로고침 중지');
    }
}

// 초기화
window.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 트레이더 마크 대시보드 시작');
    
    // 초기 데이터 로드
    loadData().then(data => {
        if (data) {
            // 자동 새로고침 시작 (10초 간격)
            startAutoRefresh(10000);
        }
    });
    
    // 페이지 떠날 때 정리
    window.addEventListener('beforeunload', stopAutoRefresh);
});

// 수동 새로고침 함수 (전역)
window.loadData = loadData;
window.startAutoRefresh = startAutoRefresh;
window.stopAutoRefresh = stopAutoRefresh;
</script>
</body>
</html>'''