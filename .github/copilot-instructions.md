# 🤖 GitHub Copilot Instructions - Algorithmic Trading Bot

> **Professional Development Guidelines for Advanced Algorithmic Trading System**

---

## 🎯 Project Mission & Vision

### Mission Statement
Develop and maintain a production-grade algorithmic trading system that combines cutting-edge machine learning with robust risk management for consistent, profitable trading in financial markets.

### Vision
Create a scalable, modular, and maintainable trading platform that serves as a foundation for:
- Advanced trading strategy development
- Real-time market analysis and execution
- Risk-aware portfolio management
- Continuous learning and adaptation

---

## 🏗️ Architectural Principles

### Core Design Philosophy
1. **Modularity**: Each component should be independent and interchangeable
2. **Scalability**: System must handle increasing data volumes and complexity
3. **Reliability**: Zero-downtime trading with robust error handling
4. **Security**: Financial-grade security for all operations
5. **Observability**: Comprehensive logging and monitoring

### Technology Stack Rationale
- **Python 3.8+**: ML ecosystem, data science libraries, rapid prototyping
- **Node.js 16+**: Real-time trading execution, IB API integration
- **Flask**: Lightweight API framework with WebSocket support
- **SQLite/PostgreSQL**: Data persistence with migration path
- **LightGBM**: High-performance gradient boosting for financial ML
- **Optuna**: Bayesian optimization for hyperparameter tuning

---

## 📁 Project Structure & Conventions

```
algorithmic-trading-bot/
├── 🎯 agent/                    # Trading execution layer
│   ├── trading_agent.js        # Main trading logic
│   ├── state_manager.js        # Position and state management
│   ├── risk_manager.js         # Real-time risk controls
│   └── order_manager.js        # Order execution and monitoring
├── 🧠 src/                      # Core Python modules
│   ├── data/                   # Data pipeline
│   │   ├── collectors/         # Data ingestion
│   │   ├── processors/         # Data cleaning & validation
│   │   └── validators/         # Data quality checks
│   ├── features/               # Feature engineering
│   │   ├── technical/          # Technical indicators
│   │   ├── fundamental/        # Fundamental features
│   │   └── alternative/        # Alternative data sources
│   ├── models/                 # ML pipeline
│   │   ├── training/           # Model training logic
│   │   ├── evaluation/         # Model validation
│   │   └── deployment/         # Model serving
│   ├── strategies/             # Trading strategies
│   │   ├── base/              # Base strategy classes
│   │   ├── trend/             # Trend following strategies
│   │   └── mean_reversion/     # Mean reversion strategies
│   ├── risk/                   # Risk management
│   │   ├── portfolio/         # Portfolio-level risk
│   │   ├── position/          # Position-level risk
│   │   └── market/            # Market risk assessment
│   └── utils/                  # Shared utilities
├── 📊 data/                     # Data storage
├── 🧪 tests/                    # Comprehensive test suite
├── 📚 docs/                     # Documentation
├── 🔧 scripts/                  # Automation scripts
└── 📋 configs/                  # Configuration management
```

### Naming Conventions
- **Files**: `snake_case.py`, `kebab-case.js`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Variables**: `snake_case`
- **Database tables**: `snake_case`

---

## 🔧 Development Standards

### Code Quality Standards
1. **Type Hints**: All Python functions must include type hints
2. **Docstrings**: Google-style docstrings for all public methods
3. **Error Handling**: Explicit exception handling with logging
4. **Testing**: Minimum 80% test coverage
5. **Linting**: Black, isort, flake8 for Python; ESLint for Node.js

### Enterprise-Grade Development Principles
1. **Official Documentation First**: Always consult official documentation before implementation
2. **Established Patterns**: Use proven design patterns from financial software industry
3. **Robust Error Handling**: Implement comprehensive error handling with proper logging
4. **Defensive Programming**: Validate all inputs and handle edge cases gracefully
5. **Production Readiness**: Code must be suitable for production financial environments

### Interactive Brokers Development Guidelines
- **Official API Reference**: Use https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#api-introduction as primary source
- **Connection Management**: Implement proper connection lifecycle management
- **Error Handling**: Handle IB-specific error codes and connection issues
- **Order Management**: Follow IB's order state machine and lifecycle patterns
- **Data Handling**: Respect IB's data throttling and subscription limits

### Example Code Template
```python
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class TradingStrategy:
    """Base class for trading strategies.
    
    This class provides the foundation for implementing trading strategies
    with proper risk management and position sizing.
    
    Attributes:
        name: Strategy identifier
        risk_params: Risk management parameters
    """
    
    def __init__(self, name: str, risk_params: Dict[str, float]) -> None:
        """Initialize trading strategy.
        
        Args:
            name: Unique strategy identifier
            risk_params: Risk management configuration
            
        Raises:
            ValueError: If risk parameters are invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Strategy name must be a non-empty string")
            
        self.name = name
        self.risk_params = self._validate_risk_params(risk_params)
        logger.info(f"Initialized strategy: {self.name}")
    
    def _validate_risk_params(self, params: Dict[str, float]) -> Dict[str, float]:
        """Validate risk management parameters."""
        required_keys = ['max_position_size', 'stop_loss_pct', 'take_profit_pct']
        
        for key in required_keys:
            if key not in params:
                raise ValueError(f"Missing required risk parameter: {key}")
                
        return params
```

---

## 🧠 Machine Learning Best Practices

### Model Development Lifecycle
1. **Data Validation**: Comprehensive data quality checks
2. **Feature Engineering**: Domain-specific financial features
3. **Model Selection**: Cross-validation with time-series splits
4. **Hyperparameter Optimization**: Bayesian optimization with Optuna
5. **Backtesting**: Walk-forward analysis with realistic constraints
6. **Model Monitoring**: Performance tracking and drift detection

### Financial ML Considerations
- **Look-ahead Bias**: Strict temporal data splits
- **Survivorship Bias**: Include delisted securities
- **Transaction Costs**: Model slippage and commissions
- **Market Microstructure**: Consider bid-ask spreads
- **Regime Changes**: Model adaptation to market conditions

### Feature Engineering Guidelines
```python
class FeatureEngineer:
    """Financial feature engineering with forward-looking bias prevention."""
    
    def create_technical_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicators avoiding look-ahead bias."""
        features = data.copy()
        
        # Price-based features
        features['sma_20'] = data['close'].rolling(20).mean()
        features['ema_12'] = data['close'].ewm(span=12).mean()
        features['rsi_14'] = ta.rsi(data['close'], length=14)
        
        # Volume-based features
        features['volume_sma_20'] = data['volume'].rolling(20).mean()
        features['volume_ratio'] = data['volume'] / features['volume_sma_20']
        
        # Volatility features
        features['atr_14'] = ta.atr(data['high'], data['low'], data['close'], length=14)
        features['bb_upper'], features['bb_lower'] = ta.bbands(data['close'], length=20)
        
        return features
```

### Learning Resources & Troubleshooting
- **IB Webinars**: https://www.interactivebrokers.com/en/index.php?f=4733 - Regular API webinars and tutorials
- **YouTube IB API Tutorials**: Search for "Interactive Brokers API Python tutorial" for video guides
- **Algorithmic Trading Books**:
  - "Algorithmic Trading" by Ernie Chan
  - "Quantitative Trading" by Ernie Chan
  - "Python for Finance" by Yves Hilpisch
- **Common Gateway Issues**:
  - Connection timeouts: Check firewall settings and trusted IPs
  - Authentication failures: Verify paper trading vs live account settings
  - Market data issues: Confirm subscriptions and market hours
  - Order rejections: Review precautionary settings and margin requirements
- **Development Best Practices**:
  - Always test with paper trading first
  - Implement proper error handling and logging
  - Use connection pooling for stability
  - Monitor API rate limits and pacing violations
  - Keep TWS/Gateway updated to latest versions

### Specialized Trading Communities & Resources
- **Python for Finance Discord**: https://discord.gg/python-for-finance - Active Python trading community
- **QuantLib Community**: https://github.com/lballabio/QuantLib - Open-source quantitative finance library
- **Zipline Community**: https://github.com/quantopian/zipline - Algorithmic trading library discussions
- **MetaTrader API Forums**: https://www.mql5.com/en/forum - For multi-broker API strategies
- **Interactive Brokers subreddit**: https://www.reddit.com/r/IBKR/ - User experiences and troubleshooting
- **Backtrader Community**: https://community.backtrader.com/ - Python backtesting framework
- **TradingView Community**: https://www.tradingview.com/support/categories/api/ - Charting and API integration
- **Alpha Architect Blog**: https://alphaarchitect.com/blog/ - Quantitative research and strategies
- **Quantocracy**: https://quantocracy.com/ - Aggregated quantitative finance content
- **Two Sigma Open Source**: https://github.com/twosigma - Professional quant tools and libraries

### Technical Tools & Integration Resources
- **Docker for Trading Systems**: https://hub.docker.com/search?q=trading - Containerized trading environments
- **Kubernetes Trading Deployments**: https://github.com/kubernetes/examples - Scalable trading system deployment
- **Redis for Trading Data**: https://redis.io/docs/use-cases/financial-services/ - High-performance data caching
- **InfluxDB Time Series**: https://www.influxdata.com/solutions/financial-services/ - Financial time-series database
- **Apache Kafka Trading**: https://kafka.apache.org/uses#financial_services - Real-time data streaming
- **Prometheus Monitoring**: https://prometheus.io/docs/instrumenting/exporters/ - System monitoring for trading
- **Grafana Dashboards**: https://grafana.com/solutions/financial-services/ - Trading system visualization
- **Jenkins CI/CD for Trading**: https://www.jenkins.io/ - Automated deployment and testing
- **AWS Financial Services**: https://aws.amazon.com/financial-services/ - Cloud infrastructure for trading
- **Google Cloud Trading Solutions**: https://cloud.google.com/solutions/financial-services - Professional trading infrastructure
- **FIX Protocol**: Understanding of Financial Information eXchange protocol standards
  - Standard message formats for trade communication
  - Order lifecycle management (New → PartiallyFilled → Filled → Cancelled)
  - Error handling and rejection codes
  
- **Order Types**: Implement standard financial order types
  ```javascript
  // Standard order types
  const ORDER_TYPES = {
    MARKET: 'MKT',     // Execute immediately at best available price
    LIMIT: 'LMT',      // Execute only at specified price or better
    STOP: 'STP',       // Trigger market order when price reached
    STOP_LIMIT: 'STP LMT', // Trigger limit order when price reached
    TRAIL: 'TRAIL',    // Trailing stop order
    MOC: 'MOC',        // Market on Close
    LOC: 'LOC'         // Limit on Close
  };
  ```

- **Position Management**: Follow industry-standard position tracking
  ```python
  class Position:
      def __init__(self):
          self.symbol = ""
          self.quantity = 0
          self.avg_price = 0.0
          self.market_value = 0.0
          self.unrealized_pnl = 0.0
          self.realized_pnl = 0.0
          
      def calculate_pnl(self, current_price: float) -> float:
          """Calculate P&L using standard financial formulas"""
          return (current_price - self.avg_price) * self.quantity
  ```

- **Settlement Cycles**: Respect standard settlement periods
  - **T+2**: Stocks settle 2 business days after trade
  - **T+1**: Government bonds settle next business day
  - **T+0**: Cash and money market instruments settle same day
  
- **Market Sessions**: Handle different trading sessions
  ```python
  MARKET_SESSIONS = {
      'PRE_MARKET': {'start': '04:00', 'end': '09:30'},
      'REGULAR': {'start': '09:30', 'end': '16:00'},
      'AFTER_HOURS': {'start': '16:00', 'end': '20:00'}
  }
  ```

- **Risk Controls**: Implement standard risk management
  - **Position Limits**: Maximum position size per symbol
  - **Exposure Limits**: Maximum portfolio exposure
  - **Loss Limits**: Daily/monthly loss thresholds
  - **Concentration Limits**: Maximum percentage in single position

---

## 🛡️ Risk Management Framework

### Multi-Layer Risk Controls
1. **Pre-Trade Risk**: Position sizing, exposure limits
2. **Intra-Trade Risk**: Stop-loss, take-profit orders
3. **Post-Trade Risk**: Portfolio rebalancing, correlation monitoring
4. **System Risk**: Circuit breakers, kill switches

### Risk Metrics Monitoring
- **Value at Risk (VaR)**: 1-day, 1% VaR calculation
- **Expected Shortfall**: Tail risk measurement
- **Maximum Drawdown**: Peak-to-trough decline tracking
- **Sharpe Ratio**: Risk-adjusted return measurement
- **Beta**: Market correlation analysis

---

## 🔄 Continuous Integration/Deployment

### CI/CD Pipeline
1. **Code Quality**: Automated linting, type checking
2. **Testing**: Unit tests, integration tests, end-to-end tests
3. **Security**: Dependency scanning, secret detection
4. **Performance**: Backtesting validation, latency testing
5. **Deployment**: Blue-green deployment with rollback capability

### Monitoring & Alerting
- **System Health**: CPU, memory, disk usage
- **Trading Performance**: PnL, drawdown, trade frequency
- **Data Quality**: Missing data, anomaly detection
- **Risk Metrics**: Position exposure, correlation changes

---

## 📊 Data Management Strategy

### Data Pipeline Architecture
1. **Ingestion**: Real-time and batch data collection
2. **Validation**: Data quality and completeness checks
3. **Storage**: Time-series optimized storage
4. **Processing**: Feature engineering and aggregation
5. **Serving**: Low-latency data access for trading

### Data Sources Integration
- **Market Data**: Primary (IB), secondary (Yahoo Finance)
- **Fundamental Data**: Company financials, economic indicators
- **Alternative Data**: News sentiment, social media, satellite data
- **Risk Data**: VIX, credit spreads, currency volatility

### Interactive Brokers API Integration
- **Primary Documentation**: Always refer to official IB TWS API documentation at https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#api-introduction
- **Modular Documentation**: IB documentation is organized in sections with specific URLs - always link to relevant specific sections
- **Common IB API Sections**:
  - Connection: `#connection`
  - Order Management: `#orders` 
  - Market Data: `#market-data`
  - Account Info: `#account-info`
  - Error Handling: `#error-handling`
  - Historical Data: `#historical-data`
- **API Patterns**: Use established IB connection patterns and error handling
- **Best Practices**: Follow IB's recommended practices for order management and data handling
- **Version Compatibility**: Ensure compatibility with latest TWS API versions
- **Specific References**: When referencing IB features, provide direct links to relevant documentation sections
- **Documentation Search Strategy**: If specific section not found, use fetch_webpage tool to retrieve current documentation structure

### Community Resources & Forums
- **Interactive Brokers API Forum**: https://www.interactivebrokers.com/en/index.php?f=forum&c=19 - Official IB API support forum
- **Reddit Algorithmic Trading**: https://www.reddit.com/r/algotrading/ - Active community for algorithmic trading discussions
- **Reddit Interactive Brokers**: https://www.reddit.com/r/interactivebrokers/ - IB-specific community discussions
- **QuantConnect Community**: https://www.quantconnect.com/forum/ - Algorithmic trading platform discussions
- **Elite Trader Forums**: https://www.elitetrader.com/et/forums/automated-trading.12/ - Professional trading automation discussions
- **Stack Overflow IB API**: https://stackoverflow.com/questions/tagged/interactive-brokers - Technical Q&A for IB API
- **GitHub IB API Repositories**: 
  - https://github.com/InteractiveBrokers/tws-api - Official IB TWS API repository
  - https://github.com/erdewit/ib_insync - Popular Python wrapper for IB API
- **TWS API Python Tutorials**: https://algotrading101.com/learn/interactive-brokers-python-api-native-guide/
- **IB Knowledge Base**: https://ibkr.info/article/2484 - Common API issues and solutions
- **IB Gateway Troubleshooting**: https://ibkr.info/article/2888 - Gateway-specific troubleshooting
- **Paper Trading Setup**: https://ibkr.info/article/2006 - Setting up paper trading for development

---

## 🏭 Industry Standards & Best Practices

### Code Reliability Standards
1. **Industry-Proven Libraries**: Use well-established, battle-tested libraries with strong community support
2. **Financial Standards**: Follow established financial industry patterns (FIX protocol awareness, order lifecycle management)
3. **Defensive Programming**: Implement robust error handling, input validation, and graceful degradation
4. **Production-Ready Patterns**: Use enterprise-grade design patterns suitable for financial applications
5. **Documentation-First**: All implementations must reference official documentation and established standards

### Technology Selection Criteria
- **Stability**: Choose mature technologies with proven track records in production environments
- **Documentation**: Prefer well-documented solutions with comprehensive API references
- **Community Support**: Select technologies with active communities and regular security updates
- **Financial Sector Adoption**: Prioritize tools commonly used in financial institutions
- **Regulatory Compliance**: Ensure chosen technologies support audit trails and compliance requirements

### Anti-Patterns to Avoid
- **Experimental Libraries**: Avoid bleeding-edge or alpha-stage libraries in production code
- **Custom Protocols**: Don't reinvent established financial communication protocols
- **Brittle Dependencies**: Avoid libraries with poor maintenance or unclear licensing
- **Undocumented Solutions**: Never implement critical functionality without proper documentation
- **Single Points of Failure**: Design with redundancy and fallback mechanisms

---

## 🔐 Security & Compliance

### Security Measures
1. **Authentication**: Multi-factor authentication for API access
2. **Authorization**: Role-based access control
3. **Encryption**: Data encryption at rest and in transit
4. **Audit Trail**: Comprehensive logging of all actions
5. **Network Security**: VPN, firewall configuration

### Compliance Considerations
- **Data Privacy**: GDPR compliance for EU data
- **Financial Regulations**: SEC, FINRA guidelines
- **Risk Disclosure**: Clear risk warnings and disclaimers
- **Record Keeping**: Trade records retention requirements

---

## 🚀 Performance Optimization

### System Performance
- **Database Optimization**: Proper indexing, query optimization
- **Memory Management**: Efficient data structures, garbage collection
- **Concurrent Processing**: Multi-threading for data processing
- **Caching**: Redis for frequently accessed data
- **Load Balancing**: Horizontal scaling for API endpoints

### Trading Performance
- **Latency Optimization**: Sub-second order execution
- **Market Data**: Real-time data streaming
- **Order Management**: Efficient order routing
- **Risk Calculations**: Real-time risk metric updates

---

## 📚 Documentation Standards

### Required Documentation
1. **API Documentation**: OpenAPI/Swagger specifications
2. **Architecture Documentation**: System design documents
3. **User Guides**: Setup and operation manuals
4. **Developer Guides**: Contribution guidelines
5. **Risk Documentation**: Risk model explanations

### Documentation Tools
- **Sphinx**: Python documentation generation
- **JSDoc**: JavaScript documentation
- **Markdown**: General documentation
- **PlantUML**: Architecture diagrams
- **Jupyter Notebooks**: Analysis examples

---

## 🎯 Future Roadmap

### Short-term Goals (3-6 months)
- [ ] Enhanced backtesting framework
- [ ] Real-time risk monitoring dashboard
- [ ] Advanced order types implementation
- [ ] Multi-asset trading support
- [ ] Improved error handling and recovery

### Medium-term Goals (6-12 months)
- [ ] Machine learning model ensemble
- [ ] Alternative data integration
- [ ] Portfolio optimization algorithms
- [ ] Performance attribution analysis
- [ ] Regulatory compliance automation

### Long-term Vision (12+ months)
- [ ] Multi-broker support
- [ ] Cryptocurrency trading integration
- [ ] Advanced options strategies
- [ ] Institutional-grade reporting
- [ ] Cloud-native deployment

---

## 🤝 Contribution Guidelines

### Code Review Process
1. **Feature Branch**: Create feature branch from main
2. **Development**: Follow coding standards and testing requirements
3. **Pull Request**: Comprehensive description with test coverage
4. **Review**: Peer review focusing on security and performance
5. **Merge**: Squash merge with descriptive commit message

### Quality Gates
- All tests must pass
- Code coverage above 80%
- No security vulnerabilities
- Performance benchmarks met
- Documentation updated

---

## 🛠️ Development Tools & Environment

### Required Tools
- **IDE**: VS Code with Python and Node.js extensions
- **Version Control**: Git with conventional commits
- **Database**: SQLite for development, PostgreSQL for production
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with JSON format

### Environment Setup
```bash
# Python environment
python -m venv trading_env
source trading_env/bin/activate  # Linux/Mac
trading_env\Scripts\activate     # Windows
pip install -r requirements.txt

# Node.js environment
npm install
npm run dev

# Pre-commit hooks
pre-commit install
```

---

## 📋 Configuration Management

### Environment-Specific Configs
- **Development**: Local SQLite, simulated trading
- **Staging**: Replica production data, paper trading
- **Production**: Live data, real trading with safeguards

### Configuration Structure
```json
{
  "environment": "production",
  "trading": {
    "mode": "live",
    "max_position_size": 0.1,
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04
  },
  "risk": {
    "max_portfolio_risk": 0.05,
    "max_sector_exposure": 0.3,
    "var_confidence": 0.99
  },
  "monitoring": {
    "alert_thresholds": {
      "drawdown": 0.03,
      "daily_loss": 0.01
    }
  }
}
```

---

## ⚠️ Critical Development Guidelines

### Financial System Requirements
1. **Accuracy**: Financial calculations must be precise
2. **Reliability**: System must handle market volatility
3. **Transparency**: All decisions must be auditable
4. **Compliance**: Adhere to financial regulations
5. **Risk Management**: Never compromise on risk controls

### Development Priorities
1. **Security First**: Never compromise on security
2. **Risk Management**: Implement multiple safety layers
3. **Testing**: Comprehensive testing before deployment
4. **Monitoring**: Real-time system health monitoring
5. **Documentation**: Keep documentation current

### Implementation Standards
1. **Use Established Libraries**: Always prefer well-documented, industry-standard libraries
2. **Follow Official Documentation**: Reference official APIs and avoid undocumented features
3. **Implement Robust Error Handling**: Plan for network failures, API timeouts, and data corruption
4. **Design for Production**: Code should be production-ready from day one
5. **Maintainable Architecture**: Write code that can be easily understood and modified

---


## Configuration
All settings and paths are managed in `system_config.json` and loaded via `load_system_config()`.

## Error Handling & Logging
All modules include error handling and detailed logging for monitoring and debugging.

## Coding Principles
- Clean, modular, and well-documented code.
- Clear separation between data collection, preprocessing, feature engineering, model training, API, and trading logic.
- Use of popular, well-supported libraries.
- Error handling and logging in all components.

---

For detailed documentation of a specific module or file, see its respective docstring or README section.

# הנחיות לשימוש יעיל ב-GitHub Copilot

## טכניקות לעריכת קוד ללא תקיעות

כאשר GitHub Copilot מבצע עריכות בקבצים גדולים או מורכבים, לעתים הפעולות עלולות להיתקע או להתבטל. הנה מספר טכניקות יעילות שיעזרו להימנע מבעיות:

### 1. העדף שימוש ב-`replace_string_in_file` על פני כלים אחרים

הכלי `replace_string_in_file` הוא היציב ביותר לעריכת קבצים. הוא מתמקד בהחלפת טקסט מוגדר היטב, מה שמפחית את הסיכוי לתקלות.

```
replace_string_in_file({
  filePath: "путь/к/файлу",
  oldString: "טקסט ישן עם הקשר מספיק",
  newString: "טקסט חדש",
  explanation: "הסבר על העריכה"
})
```

### 2. הוסף הקשר מספיק לזיהוי המיקום הנכון

כאשר משתמשים ב-`replace_string_in_file`, חשוב לכלול מספיק שורות לפני ואחרי החלק שרוצים לערוך, כדי לזהות באופן ייחודי את המיקום בקובץ:

- **מומלץ**: לכלול 3-5 שורות של הקשר לפני ואחרי הטקסט לעריכה
- **הימנע**: מלהשתמש בחלקי קוד קצרים מדי שעלולים להופיע במקומות רבים בקובץ

דוגמה טובה:
```
// הקשר לפני
function someExistingFunction() {
  // הקוד שרוצים להחליף
  let x = 1;
  console.log(x);
  // עוד קוד להחלפה
}
// הקשר אחרי
```

### 3. פצל עריכות גדולות לשלבים קטנים

במקום לנסות לבצע שינוי גדול בבת אחת, שעלול להיתקע:

1. פצל את העריכה למספר שינויים קטנים וממוקדים
2. בצע כל שינוי בנפרד
3. ודא שכל שלב הושלם בהצלחה לפני המעבר לשלב הבא

### 4. בדוק את תוכן הקובץ לפני העריכה

השתמש ב-`read_file` כדי לוודא את מבנה הקובץ והתוכן שלו לפני ביצוע שינויים:

```
read_file({
  filePath: "путь/к/файлу",
  startLine: 100,
  endLine: 150
})
```

זה יעזור לך לזהות את המיקום המדויק ולכתוב חיפוש טקסט מדויק יותר.

### 5. הימנע משימוש בדפוסי חיפוש עמומים

- **טוב**: חיפוש מחרוזת מדויקת עם הקשר מספיק
- **פחות טוב**: שימוש בתבניות רגקס מורכבות או בתבניות עמומות

### 6. טפל בתוכן דינמי בזהירות

אם יש חלקים בקוד שעשויים להשתנות (כמו תאריכים, מזהים אקראיים):

1. התמקד בחלקים סטטיים לזיהוי המיקום
2. עדיף להחליף חלק קטן יותר אבל מדויק יותר

### 7. שיטת ה"זיהוי ייחודי"

כשעובדים עם קבצים גדולים מאוד, השתמש בשיטת זיהוי ייחודי:
1. זהה תבנית ייחודית בקוד (כמו שם פונקציה)
2. קרא את הקובץ עם `read_file` כדי למצוא את המיקום המדויק
3. השתמש בטווח השורות המדויק בעריכה הבאה

### סיכום

שילוב הטכניקות האלה יעזור להימנע מבעיות עריכה, במיוחד בפרויקטים גדולים. גישה מדורגת ומתוכננת היטב מובילה לתוצאות הטובות ביותר כשעובדים עם GitHub Copilot.
