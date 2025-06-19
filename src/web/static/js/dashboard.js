// Dashboard JavaScript for ML Portfolio Analyzer

class PortfolioDashboard {
    constructor() {
        this.apiBaseUrl = '/api';
        this.charts = {};
        this.websocket = null;
        this.authToken = localStorage.getItem('authToken');
        
        this.init();
    }
    
    async init() {
        await this.loadPortfolios();
        await this.loadMarketData();
        this.initializeCharts();
        this.setupEventListeners();
        this.connectWebSocket();
    }
    
    // API Methods
    async makeRequest(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    // Portfolio Management
    async loadPortfolios() {
        try {
            const data = await this.makeRequest(`${this.apiBaseUrl}/portfolio/`);
            this.renderPortfolios(data.portfolios);
        } catch (error) {
            console.error('Failed to load portfolios:', error);
            this.showAlert('Failed to load portfolios', 'error');
        }
    }
    
    renderPortfolios(portfolios) {
        const container = document.getElementById('portfolios-container');
        if (!container) return;
        
        container.innerHTML = portfolios.map(portfolio => `
            <div class="card portfolio-card" data-portfolio-id="${portfolio.id}">
                <h3>${portfolio.name}</h3>
                <p class="portfolio-description">${portfolio.description || 'No description'}</p>
                <div class="portfolio-value">$${portfolio.total_value.toLocaleString()}</div>
                <div class="portfolio-change ${portfolio.performance.daily_change >= 0 ? 'positive' : 'negative'}">
                    ${portfolio.performance.daily_change >= 0 ? '+' : ''}${portfolio.performance.daily_change.toFixed(2)}%
                </div>
                <div class="portfolio-actions">
                    <button class="btn btn-secondary" onclick="dashboard.viewPortfolio('${portfolio.id}')">
                        View Details
                    </button>
                    <button class="btn" onclick="dashboard.analyzePortfolio('${portfolio.id}')">
                        Analyze
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    // Market Data
    async loadMarketData() {
        const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA'];
        const marketDataContainer = document.getElementById('market-data-container');
        
        if (!marketDataContainer) return;
        
        try {
            const marketData = await Promise.all(
                symbols.map(symbol => this.makeRequest(`${this.apiBaseUrl}/market-data/${symbol}`))
            );
            
            this.renderMarketData(marketData);
        } catch (error) {
            console.error('Failed to load market data:', error);
            this.showAlert('Failed to load market data', 'error');
        }
    }
    
    renderMarketData(marketData) {
        const container = document.getElementById('market-data-container');
        if (!container) return;
        
        container.innerHTML = `
            <h3>Market Overview</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>Change</th>
                        <th>Volume</th>
                    </tr>
                </thead>
                <tbody>
                    ${marketData.map(data => `
                        <tr>
                            <td><strong>${data.symbol}</strong></td>
                            <td>$${data.price.toFixed(2)}</td>
                            <td class="${data.change >= 0 ? 'positive' : 'negative'}">
                                ${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)} 
                                (${data.change_percent.toFixed(2)}%)
                            </td>
                            <td>${data.volume.toLocaleString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    // Charts
    initializeCharts() {
        this.createPortfolioCompositionChart();
        this.createPerformanceChart();
    }
    
    createPortfolioCompositionChart() {
        const ctx = document.getElementById('portfolio-composition-chart');
        if (!ctx) return;
        
        const data = {
            labels: ['Technology', 'Healthcare', 'Financial', 'Consumer', 'Energy'],
            datasets: [{
                data: [35, 25, 20, 15, 5],
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#f5576c',
                    '#4facfe'
                ]
            }]
        };
        
        this.charts.composition = new Chart(ctx, {
            type: 'pie',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    createPerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx) return;
        
        const data = {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Portfolio Performance',
                data: [100, 105, 102, 108, 112, 115],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }]
        };
        
        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }
    
    // WebSocket for Real-time Updates
    connectWebSocket() {
        if (!this.authToken) return;
        
        const wsUrl = `ws://localhost:8000/ws/portfolio_1`;
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'portfolio_data':
                this.updatePortfolioDisplay(data.data);
                break;
            case 'price_update':
                this.updatePriceDisplay(data.data);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }
    
    updateConnectionStatus(isConnected) {
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            indicator.className = `status-indicator ${isConnected ? 'online' : 'offline'}`;
            indicator.title = isConnected ? 'Connected' : 'Disconnected';
        }
    }
    
    // Event Handlers
    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }
        
        // Portfolio creation form
        const createPortfolioForm = document.getElementById('create-portfolio-form');
        if (createPortfolioForm) {
            createPortfolioForm.addEventListener('submit', this.handleCreatePortfolio.bind(this));
        }
        
        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', this.handleLogout.bind(this));
        }
    }
    
    async handleLogin(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        
        try {
            const response = await this.makeRequest(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                body: JSON.stringify({
                    email: formData.get('email'),
                    password: formData.get('password')
                })
            });
            
            this.authToken = response.access_token;
            localStorage.setItem('authToken', this.authToken);
            
            this.showAlert('Login successful!', 'success');
            window.location.reload();
            
        } catch (error) {
            console.error('Login failed:', error);
            this.showAlert('Login failed. Please check your credentials.', 'error');
        }
    }
    
    handleLogout() {
        localStorage.removeItem('authToken');
        this.authToken = null;
        if (this.websocket) {
            this.websocket.close();
        }
        window.location.reload();
    }
    
    async handleCreatePortfolio(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        
        try {
            await this.makeRequest(`${this.apiBaseUrl}/portfolio/`, {
                method: 'POST',
                body: JSON.stringify({
                    name: formData.get('name'),
                    description: formData.get('description')
                })
            });
            
            this.showAlert('Portfolio created successfully!', 'success');
            await this.loadPortfolios();
            event.target.reset();
            
        } catch (error) {
            console.error('Failed to create portfolio:', error);
            this.showAlert('Failed to create portfolio', 'error');
        }
    }
    
    // Utility Methods
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) return;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        alertContainer.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
    
    async viewPortfolio(portfolioId) {
        try {
            const portfolio = await this.makeRequest(`${this.apiBaseUrl}/portfolio/${portfolioId}`);
            // Implement portfolio detail view
            console.log('Portfolio details:', portfolio);
        } catch (error) {
            console.error('Failed to load portfolio details:', error);
            this.showAlert('Failed to load portfolio details', 'error');
        }
    }
    
    async analyzePortfolio(portfolioId) {
        try {
            // Get portfolio holdings and analyze each symbol
            const portfolio = await this.makeRequest(`${this.apiBaseUrl}/portfolio/${portfolioId}`);
            const symbols = portfolio.holdings.map(h => h.symbol);
            
            for (const symbol of symbols) {
                const analysis = await this.makeRequest(`${this.apiBaseUrl}/analysis/${symbol}`, {
                    method: 'POST',
                    body: JSON.stringify({
                        indicators: ['sma', 'rsi', 'macd'],
                        period: 30
                    })
                });
                
                console.log(`Analysis for ${symbol}:`, analysis);
            }
            
            this.showAlert('Portfolio analysis completed!', 'success');
        } catch (error) {
            console.error('Analysis failed:', error);
            this.showAlert('Portfolio analysis failed', 'error');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PortfolioDashboard();
});