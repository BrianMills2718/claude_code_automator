// WebSocket client for real-time updates

class WebSocketClient {
    constructor(portfolioId) {
        this.portfolioId = portfolioId;
        this.websocket = null;
        this.reconnectInterval = 5000;
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        
        this.connect();
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/ws/${this.portfolioId}`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            this.setupEventListeners();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }
    
    setupEventListeners() {
        this.websocket.onopen = () => {
            console.log(`WebSocket connected for portfolio ${this.portfolioId}`);
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            this.onConnect();
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        this.websocket.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            this.updateConnectionStatus(false);
            this.onDisconnect();
            
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
            this.onError(error);
        };
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'portfolio_data':
                this.onPortfolioData(data.data, data.timestamp);
                break;
            case 'price_update':
                this.onPriceUpdate(data.data, data.timestamp);
                break;
            case 'market_alert':
                this.onMarketAlert(data.data, data.timestamp);
                break;
            default:
                console.warn('Unknown WebSocket message type:', data.type);
        }
    }
    
    send(data) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket is not connected, cannot send message');
        }
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        
        setTimeout(() => {
            if (this.reconnectAttempts <= this.maxReconnectAttempts) {
                this.connect();
            }
        }, this.reconnectInterval);
    }
    
    updateConnectionStatus(isConnected) {
        const statusElement = document.getElementById('ws-connection-status');
        if (statusElement) {
            statusElement.className = `status-indicator ${isConnected ? 'online' : 'offline'}`;
            statusElement.title = isConnected ? 'Real-time data connected' : 'Real-time data disconnected';
        }
        
        // Update status text
        const statusText = document.getElementById('ws-status-text');
        if (statusText) {
            statusText.textContent = isConnected ? 'Live' : 'Offline';
        }
    }
    
    // Event callbacks (to be overridden)
    onConnect() {
        // Override in implementation
        console.log('WebSocket connected');
    }
    
    onDisconnect() {
        // Override in implementation
        console.log('WebSocket disconnected');
    }
    
    onError(error) {
        // Override in implementation
        console.error('WebSocket error:', error);
    }
    
    onPortfolioData(data, timestamp) {
        // Override in implementation
        console.log('Portfolio data received:', data);
        
        // Update portfolio value display
        const valueElement = document.getElementById('portfolio-total-value');
        if (valueElement && data.total_value) {
            valueElement.textContent = `$${data.total_value.toLocaleString()}`;
        }
        
        // Update daily change
        const changeElement = document.getElementById('portfolio-daily-change');
        if (changeElement && data.daily_change !== undefined) {
            changeElement.textContent = `${data.daily_change >= 0 ? '+' : ''}${data.daily_change.toFixed(2)}%`;
            changeElement.className = `portfolio-change ${data.daily_change >= 0 ? 'positive' : 'negative'}`;
        }
        
        // Update holdings table
        if (data.holdings) {
            this.updateHoldingsTable(data.holdings);
        }
    }
    
    onPriceUpdate(data, timestamp) {
        // Override in implementation
        console.log('Price update received:', data);
        
        // Update individual stock prices in the holdings table
        Object.entries(data).forEach(([symbol, priceData]) => {
            const priceElement = document.getElementById(`price-${symbol}`);
            if (priceElement) {
                priceElement.textContent = `$${priceData.price.toFixed(2)}`;
            }
            
            const changeElement = document.getElementById(`change-${symbol}`);
            if (changeElement) {
                changeElement.textContent = `${priceData.change >= 0 ? '+' : ''}${priceData.change.toFixed(2)}`;
                changeElement.className = priceData.change >= 0 ? 'positive' : 'negative';
            }
        });
        
        // Update last update timestamp
        const timestampElement = document.getElementById('last-update-time');
        if (timestampElement) {
            const updateTime = new Date(timestamp);
            timestampElement.textContent = updateTime.toLocaleTimeString();
        }
    }
    
    onMarketAlert(data, timestamp) {
        // Override in implementation
        console.log('Market alert received:', data);
        
        // Show alert notification
        this.showNotification(data.message, data.type || 'info');
    }
    
    updateHoldingsTable(holdings) {
        const tableBody = document.getElementById('holdings-table-body');
        if (!tableBody) return;
        
        tableBody.innerHTML = holdings.map(holding => `
            <tr>
                <td><strong>${holding.symbol}</strong></td>
                <td>${holding.shares}</td>
                <td id="price-${holding.symbol}">$${holding.price?.toFixed(2) || '0.00'}</td>
                <td id="change-${holding.symbol}" class="${holding.change >= 0 ? 'positive' : 'negative'}">
                    ${holding.change >= 0 ? '+' : ''}${holding.change?.toFixed(2) || '0.00'}
                </td>
                <td>$${(holding.shares * (holding.price || 0)).toFixed(2)}</td>
            </tr>
        `).join('');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.textContent = message;
        
        // Add to notification container
        const container = document.getElementById('notification-container') || document.body;
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Export for use in other modules
window.WebSocketClient = WebSocketClient;